#!/usr/bin/env python3
"""Ticket records -> crowding estimates by route, direction, stretch, day type and hour.

Usage:
  python pipeline.py --tickets data/October-Delhi.csv --routes data/routes_stops.csv --out out

Inputs
  tickets : CSV with passenger_count, amount, vehicle_number, ticket_type_id, start_stop_name,
            end_stop_name, route (e.g. 8UP), created_at (IST), is_ac
  routes  : CSV with route, seq, stop_name, lat, lon, cum_min  (stop order + cumulative minutes
            from the first stop). Derive from static GTFS (stop_times + stops).
Outputs (in --out)
  crowding_by_stretch.csv, crowding_by_route_hour.csv, qa_checks.json
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

SEATS = 35            # assumed seated capacity of a standard bus (override per route if known)
LEVELS = ["Seats available", "Standing room", "Crowded"]


def norm(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.lower()


def level_of(load, seats=SEATS):
    """0 = seats available, 1 = standing room, 2 = crowded (thresholds are assumptions)."""
    return np.where(load < 0.85 * seats, 0, np.where(load < 1.7 * seats, 1, 2))


def confidence_of(n):
    return np.where(n >= 20, "high", np.where(n >= 8, "medium", "low"))


def run(tickets_path, routes_path, out_dir, uplift, gap_min, seats):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rs = pd.read_csv(routes_path)
    rs["key"] = norm(rs["stop_name"])
    nstops = rs.groupby("route")["seq"].max() + 1
    cum = {r: g.sort_values("seq")["cum_min"].to_numpy() for r, g in rs.groupby("route")}

    t = pd.read_csv(tickets_path)
    n_raw = len(t)
    valid_routes = set(rs["route"].unique())
    t = t[t["route"].isin(valid_routes)].copy()
    t["created_at"] = pd.to_datetime(t["created_at"], errors="coerce").dt.tz_localize(None)
    t = t.dropna(subset=["created_at", "route", "start_stop_name", "vehicle_number"]).copy()
    t["pax"] = pd.to_numeric(t["passenger_count"], errors="coerce").fillna(1).clip(lower=1)

    # --- map stop names to positions on the route -------------------------------------------
    m = rs[["route", "key", "seq"]]
    t["skey"], t["ekey"] = norm(t["start_stop_name"]), norm(t["end_stop_name"])
    t = t.merge(m.rename(columns={"key": "skey", "seq": "b"}), on=["route", "skey"], how="left")
    t = t.merge(m.rename(columns={"key": "ekey", "seq": "e"}), on=["route", "ekey"], how="left")
    n_unmatched = int(t["b"].isna().sum())
    t = t.dropna(subset=["b"]).copy()
    t["b"] = t["b"].astype(int)

    # --- alighting: use stated end stop if it is downstream, else impute median ride length ---
    valid = t["e"].notna() & (t["e"] > t["b"])
    med = (t[valid].assign(r=lambda d: d["e"] - d["b"]).groupby("route")["r"].median()
           .round().clip(lower=1))
    t["e_imp"] = np.where(valid, t["e"], t["b"] + t["route"].map(med).fillna(2))
    t["e_imp"] = np.minimum(t["e_imp"], t["route"].map(nstops) - 1).astype(int)
    t = t[t["e_imp"] > t["b"]].copy()

    # --- split into bus trips: same vehicle+route, new trip after a quiet gap -----------------
    t = t.sort_values(["route", "vehicle_number", "created_at"])
    gap = t.groupby(["route", "vehicle_number"])["created_at"].diff()
    t["trip"] = ((gap.isna()) | (gap > pd.Timedelta(minutes=gap_min))).cumsum()

    frames = []
    for route, g in t.groupby("route"):
        S = int(nstops[route]) - 1                   # number of stretches
        cm = cum[route]
        tid, uniq = pd.factorize(g["trip"])
        T = len(uniq)
        mat = np.zeros((T, S + 1))
        np.add.at(mat, (tid, g["b"].to_numpy()), g["pax"].to_numpy())
        np.add.at(mat, (tid, g["e_imp"].to_numpy()), -g["pax"].to_numpy())
        load = np.cumsum(mat, axis=1)[:, :S] * uplift      # people on board on each stretch
        # trip start at first stop = median of (ticket time - minutes from first stop)
        adj = g["created_at"] - pd.to_timedelta(cm[g["b"].to_numpy()], unit="m")
        start = pd.Series(adj.to_numpy()).groupby(tid).median()
        start = pd.to_datetime(start).to_numpy(dtype="datetime64[ns]")
        tm = start[:, None] + (cm[:S][None, :] * 60 * 1e9).astype("timedelta64[ns]")
        tm = pd.to_datetime(tm.ravel())
        frames.append(pd.DataFrame({
            "route": route, "stretch": np.tile(np.arange(S), T), "load": load.ravel(),
            "hour": tm.hour, "weekday": tm.dayofweek < 5, "week": (tm.day - 1) // 7}))
    L = pd.concat(frames, ignore_index=True)
    L["daytype"] = np.where(L["weekday"], "weekday", "weekend")

    # --- aggregate ----------------------------------------------------------------------------
    grp = L.groupby(["route", "stretch", "daytype", "hour"])["load"]
    agg = grp.agg(mean_load="mean", p80_load=lambda x: x.quantile(0.8), n_trips="size").reset_index()
    names = rs.set_index(["route", "seq"])["stop_name"]
    agg["from_stop"] = [names[(r, s)] for r, s in zip(agg["route"], agg["stretch"])]
    agg["to_stop"] = [names[(r, s + 1)] for r, s in zip(agg["route"], agg["stretch"])]
    agg["level"] = level_of(agg["mean_load"], seats)
    agg["level_label"] = [LEVELS[i] for i in agg["level"]]
    agg["confidence"] = confidence_of(agg["n_trips"])
    agg = agg.round({"mean_load": 1, "p80_load": 1})
    agg.to_csv(out / "crowding_by_stretch.csv", index=False)

    # operator view: worst stretch per route/daytype/hour
    idx = agg.groupby(["route", "daytype", "hour"])["mean_load"].idxmax()
    ops = agg.loc[idx, ["route", "daytype", "hour", "from_stop", "to_stop", "mean_load",
                        "p80_load", "level_label", "n_trips", "confidence"]]
    ops.to_csv(out / "crowding_by_route_hour.csv", index=False)

    # --- checks against known patterns --------------------------------------------------------
    wd = L[L["weekday"]].groupby("hour")["load"].mean()
    peak = wd[(wd.index.isin([8, 9, 10])) | (wd.index.isin([17, 18, 19]))].mean()
    mid = wd[wd.index.isin([12, 13, 14])].mean()
    wk_end = L[~L["weekday"]]["load"].mean()
    wk_day = L[L["weekday"]]["load"].mean()
    w = L[L["weekday"]].groupby(["route", "stretch", "hour", L["week"] % 2])["load"].mean().unstack()
    stab = float(w.dropna().corr().iloc[0, 1]) if w.shape[1] == 2 else None
    top = agg[agg["daytype"] == "weekday"].nlargest(5, "mean_load")[
        ["route", "from_stop", "to_stop", "hour", "mean_load"]].to_dict("records")
    qa = {
        "tickets_read": int(n_raw), "tickets_dropped_unmatched_stop": n_unmatched,
        "tickets_used": int(len(t)), "trips_built": int(t["trip"].nunique()),
        "uplift_for_unticketed_riders": uplift, "assumed_seats": seats,
        "weekday_peak_vs_midday_load_ratio": round(float(peak / mid), 2) if mid else None,
        "weekday_busiest_hours": [int(h) for h in wd.nlargest(3).index],
        "weekday_vs_weekend_load_ratio": round(float(wk_day / wk_end), 2) if wk_end else None,
        "week_to_week_stability_corr_odd_vs_even_weeks": None if stab is None else round(stab, 3),
        "busiest_weekday_stretches": top,
        "share_of_cells_low_confidence": round(float((agg["confidence"] == "low").mean()), 3),
    }
    (out / "qa_checks.json").write_text(json.dumps(qa, indent=2, default=str))
    print(json.dumps(qa, indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True)
    ap.add_argument("--routes", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--uplift", type=float, default=1.15,
                    help="multiplier for riders with no ticket (pass holders etc.); assumption")
    ap.add_argument("--gap-min", type=float, default=20, help="quiet gap that starts a new trip")
    ap.add_argument("--seats", type=int, default=SEATS)
    a = ap.parse_args()
    run(a.tickets, a.routes, a.out, a.uplift, a.gap_min, a.seats)
