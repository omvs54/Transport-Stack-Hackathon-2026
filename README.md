# Crowd-aware Bus Planner — Delhi Transport Stack Hackathon (Problem 02)

Uses DTC ticket data to estimate how crowded each bus is, by route/stretch/hour. Shows crowdedness alongside travel time so riders can pick the fastest or the most comfortable option.

🚀 **Live Prototype Demo:** [https://transport-stack-hackathon-2026.onrender.com](https://transport-stack-hackathon-2026.onrender.com)

---

## Prototype Status & Delhi Transport Stack API Access
- **Current Stage**: This working prototype was built for the **Delhi Transport Stack Hackathon 2026 (Problem 02)**.
- **Production API Integration**: Once our request review is processed by the Delhi Transport Stack (GNCTD) team, we will integrate their official live API endpoints for real-time GTFS vehicle tracking and live ETM feed updates.
- **Data Grounding**: Until production API keys are granted, the system runs on our precomputed empirical crowding model derived from the official October 2026 Delhi DTC dataset (**2,559,899 ticket records** across **51,221 reconstructed trips**).

---

## What we found in the data
- **2,559,899** tickets from October 2026 (official DTC dataset)
- Segmented into **51,221 bus trips** (20-min quiet-gap rule)
- Peak hours carry **1.71x** the midday load — lines up with what riders report
- Odd-week vs even-week loads correlate at **89.8%**, so the pattern is stable

## How to run locally
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

## Delhi Transport Stack (DTS) API Hook
Set `DTS_API_KEY` env var (`export DTS_API_KEY="..."`) to query the official Delhi Transport Stack journey planner endpoint (`https://delhi.transportstack.in/api/serviceset/journey-planner/multi_modal`). If the key is not set or waiting on approval, the app automatically falls back to our local dataset-backed engine.

## How the model works (details in TECHNICAL_NOTE.md)
Group tickets into trips (same route + vehicle, 20-min gap = new trip), running board/alight counter per stretch, 1.15x uplift for pass-holders, then bucket into Seats / Standing / Crowded at 35-seat baseline.

## Known limitations
- Direct routes only, no transfers
- Travel time from schedule offsets, not live GPS
- Seat count + pass-holder uplift are rough assumptions
- One month of data (no festivals/monsoon)

## Sharing & Next Steps
We are looking forward to sharing this project on LinkedIn to showcase how empirical ticketing data can power commuter-centric, crowd-aware public transit planning in Delhi.

## Author & Connect
- **Author:** [Om Satarkar](https://www.linkedin.com/in/om-satarkar-2579392b8/)
- **GitHub:** [@omvs54](https://github.com/omvs54)
- **LinkedIn:** [linkedin.com/in/om-satarkar-2579392b8](https://www.linkedin.com/in/om-satarkar-2579392b8/)

## Credits
Stack: pandas · NumPy · Flask · Leaflet/OSM · gunicorn  
Data: Delhi Transport Stack (JICA / Chartr / CSM IIIT-D / ARF IIT-K).
