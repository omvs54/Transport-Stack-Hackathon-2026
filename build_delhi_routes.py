#!/usr/bin/env python3
"""Extract top Delhi routes and reconstruct valid stop sequences directly from October-Delhi.csv"""
import os
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
# Default to bundled sample, or override with full October file via env var
TICKETS_CSV = Path(os.environ.get("TICKETS_CSV", BASE_DIR / "data" / "sample_delhi_tickets.csv"))
OUT_ROUTES_CSV = BASE_DIR / "data" / "routes_stops_delhi.csv"

def build_routes(top_n=12, max_rows=800000):
    print(f"Reading up to {max_rows} rows from {TICKETS_CSV}...")
    df = pd.read_csv(TICKETS_CSV, nrows=max_rows)
    df = df.dropna(subset=["route", "start_stop_name", "end_stop_name"])
    
    top_routes = df["route"].value_counts().head(top_n).index.tolist()
    print("Selected top routes:", top_routes)
    
    records = []
    for rt in top_routes:
        sub = df[df["route"] == rt]
        stops = sorted(list(set(sub["start_stop_name"]).union(set(sub["end_stop_name"]))))
        if len(stops) < 5:
            continue
            
        pair_counts = sub.groupby(["start_stop_name", "end_stop_name"]).size().to_dict()
        
        # Tournament scoring to order stops along the linear route
        scores = {}
        for u in stops:
            score = 0
            for v in stops:
                if u != v:
                    fwd = pair_counts.get((u, v), 0)
                    rev = pair_counts.get((v, u), 0)
                    if fwd > rev:
                        score += 1
                    elif rev > fwd:
                        score -= 1
            scores[u] = score
            
        ordered = sorted(stops, key=lambda s: scores[s], reverse=True)
        # Filter stops that have very low flow or noise
        valid_stops = []
        for s in ordered:
            out_cnt = sub[sub["start_stop_name"] == s].shape[0]
            in_cnt = sub[sub["end_stop_name"] == s].shape[0]
            if out_cnt + in_cnt >= 5: # active stop
                valid_stops.append(s)
                
        if len(valid_stops) < 5:
            valid_stops = ordered
            
        # Assign estimated cumulative minutes (approx 2.5 minutes between stops)
        for seq, sname in enumerate(valid_stops):
            cum_min = round(seq * 2.5, 1)
            # Default lat/lon around Delhi center with slight progression
            lat = 28.5 + (seq * 0.005)
            lon = 77.2 + (seq * 0.005)
            records.append({
                "route": rt,
                "seq": seq,
                "stop_name": sname,
                "lat": lat,
                "lon": lon,
                "cum_min": cum_min
            })
            
    res_df = pd.DataFrame(records)
    res_df.to_csv(OUT_ROUTES_CSV, index=False)
    print(f"Saved {len(res_df)} stop entries across {res_df['route'].nunique()} routes to {OUT_ROUTES_CSV}")

if __name__ == "__main__":
    build_routes()
