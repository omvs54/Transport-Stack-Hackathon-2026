# Crowd-aware Bus Planner — Delhi Transport Stack Hackathon (Problem 02)

Uses DTC ticket data to estimate how crowded each bus is, by route/stretch/hour. Shows crowdedness alongside travel time so riders can pick the fastest or the most comfortable option.

## What we found in the data
- **2,559,899** tickets from October 2026 (official DTC dataset)
- Segmented into **51,221 bus trips** (20-min quiet-gap rule)
- Peak hours carry **1.71x** the midday load — lines up with what riders report
- Odd-week vs even-week loads correlate at **89.8%**, so the pattern is stable

## How to run
```bash
cd crowd-planner
python app.py        # opens at http://localhost:5000
```
Pick origin, destination, departure time, day type. Toggle **Fastest ↔ Most Comfortable**.

## Output files (`out/`)
| File | What it has |
|------|-------------|
| `crowding_by_stretch.csv` | Mean + p80 load per route / stretch / hour / daytype |
| `crowding_by_route_hour.csv` | Peak bottleneck stretches per route per hour |
| `qa_checks.json` | Validation stats (peak ratio, stability, busiest hours) |

## DTS API hook
Set `DTS_API_KEY` env var to hit the official Delhi Transport Stack journey planner endpoint. Without the key, falls back to local precomputed routes from the ticket data.

## How the model works (details in TECHNICAL_NOTE.md)
Group tickets into trips (same route + vehicle, 20-min gap = new trip), running board/alight counter per stretch, 1.15x uplift for pass-holders, then bucket into Seats / Standing / Crowded at 35-seat baseline.

## Known limitations
- Direct routes only, no transfers
- Travel time from schedule offsets, not live GPS
- Seat count + pass-holder uplift are rough assumptions
- One month of data (no festivals/monsoon)

## Credits
pandas · NumPy · Flask · Leaflet/OSM. Data from Delhi Transport Stack (JICA / Chartr / CSM IIIT-D / ARF IIT-K).
