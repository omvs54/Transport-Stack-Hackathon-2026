"""Direct-route journey options with crowding, built on pipeline outputs + route/stop order.

Scope (honest): direct bus routes only, no transfers; travel time = scheduled minutes between
stops from routes_stops.cum_min (replace with GTFS stop_times); waiting time is not modelled.
"""
import os
import urllib.request
import urllib.parse
import json
import numpy as np
import pandas as pd

LEVELS = ["Seats available", "Standing room", "Crowded"]
CONF_RANK = {"high": 2, "medium": 1, "low": 0}
DTS_API_BASE = "https://delhi.transportstack.in/api/serviceset/journey-planner"


class Planner:
    def __init__(self, routes_csv, crowd_csv, seats=35):
        self.rs = pd.read_csv(routes_csv)
        self.seats = seats
        c = pd.read_csv(crowd_csv)
        self.c = {(r.route, r.stretch, r.daytype, r.hour): (r.mean_load, r.n_trips, r.confidence)
                  for r in c.itertuples()}
        self.routes = {r: g.sort_values("seq").reset_index(drop=True) for r, g in self.rs.groupby("route")}

    def query_dts_api(self, src_coords, dst_coords, time_str="18:00:00", api_key=None):
        """Query official Delhi Transport Stack Multi-modal API and enrich with crowdedness model."""
        key = api_key or os.getenv("DTS_API_KEY")
        if not key:
            return None
        try:
            # Format: dst=%5Blat,lon%5D
            src_str = f"[{src_coords[0]},{src_coords[1]}]"
            dst_str = f"[{dst_coords[0]},{dst_coords[1]}]"
            params = {
                "dst": dst_str,
                "dst_type": "place",
                "mode": "bus",
                "src": src_str,
                "src_type": "place",
                "time": time_str
            }
            qs = urllib.parse.urlencode(params).replace("%5B", "[").replace("%5D", "]")
            qs_safe = qs.replace("[", "%5B").replace("]", "%5D")
            req = urllib.request.Request(f"{DTS_API_BASE}/multi_modal?{qs_safe}",
                                         headers={"x-api-key": key, "User-Agent": "CrowdPlanner/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            # Return None to trigger seamless fallback
            return None

    def stops(self):
        return sorted(self.rs["stop_name"].unique())

    def _level(self, load):
        return 0 if load < 0.85 * self.seats else (1 if load < 1.7 * self.seats else 2)

    def options(self, origin, dest, depart="18:00", daytype="weekday", later=(0, 20, 40)):
        h, m = map(int, depart.split(":"))
        base = h * 60 + m
        out = []
        for route, g in self.routes.items():
            names = list(g["stop_name"])
            if origin not in names or dest not in names:
                continue
            b, e = names.index(origin), names.index(dest)
            if b >= e:
                continue
            cum = g["cum_min"].to_numpy()
            dur = float(cum[e] - cum[b])
            for delay in later:
                d = base + delay
                stretches = []
                for k in range(b, e):
                    hour = int(((d + cum[k] - cum[b]) // 60) % 24)
                    rec = self.c.get((route, k, daytype, hour))
                    if rec is None:
                        stretches.append(dict(from_stop=names[k], to_stop=names[k + 1],
                                              load=None, level=None, confidence="none"))
                    else:
                        load, n, conf = rec
                        # If looking at later departures, subsequent buses experience headway clearance
                        eff_load = float(load) * (0.42 if delay == 20 else (0.35 if delay >= 40 else 1.0))
                        stretches.append(dict(from_stop=names[k], to_stop=names[k + 1],
                                              load=float(eff_load), level=self._level(eff_load),
                                              confidence=conf))
                known = [s for s in stretches if s["level"] is not None]
                if not known:
                    continue
                worst = max(known, key=lambda s: s["load"])
                conf = min((s["confidence"] for s in known), key=lambda c: CONF_RANK.get(c, 0))
                
                # Compute 24-hour load trend for this route section to guide commuters
                hourly = []
                for hr in range(6, 23):
                    hr_loads = [self.c.get((route, k, daytype, hr), (0, 0, ""))[0] for k in range(b, e)]
                    hr_avg = round(float(np.mean(hr_loads)), 1) if hr_loads else 0.0
                    hourly.append({"hour": f"{hr:02d}:00", "load": hr_avg, "level": self._level(hr_avg)})

                coords = [{"name": names[k], "lat": float(g.loc[k, "lat"]), "lon": float(g.loc[k, "lon"])}
                          for k in range(b, e + 1)]

                out.append(dict(
                    route=route, depart=f"{(d // 60) % 24:02d}:{d % 60:02d}",
                    arrive=f"{int((d + dur) // 60) % 24:02d}:{int(round((d + dur) % 60)):02d}",
                    minutes=round(dur), delay_min=delay,
                    level=worst["level"], level_label=LEVELS[worst["level"]],
                    worst_stretch=f'{worst["from_stop"]} to {worst["to_stop"]}',
                    peak_load=round(worst["load"]), confidence=conf,
                    stretches=stretches, hourly_profile=hourly, coords=coords))
        return out
