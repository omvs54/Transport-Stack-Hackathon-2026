# Crowd-aware Bus Planner (Delhi Transport Stack, Problem 02)

Turns Delhi bus ticket records (ETM + e-ticketing) into empirical crowdedness estimates across routes, stretches between stops, day types, and hours of the day. A clean journey planner displays expected crowdedness alongside scheduled travel time, allowing commuters to sort by **Fastest** or **Most comfortable** (avoiding crowds).

## Dataset & Model Findings
- **Data source**: Official October 2026 Delhi DTC dataset (`October-Delhi.csv`), containing **2,559,899 ticket records**.
- **Reconstructed Trips**: **51,221 bus trips** segmented across vehicles and routes using a 20-minute quiet-gap algorithm.
- **Peak vs Midday Validation**: **1.71x load ratio** during peak rush hours (8:00–10:00 AM, 17:00–20:00 PM) compared to midday off-peak (12:00–14:00).
- **Temporal Stability**: **89.8% correlation** between odd and even week load distributions, confirming consistent commuter demand patterns.
- **Confidence Rating**: Categorized into *High* (≥20 observed trips), *Medium* (≥8 trips), and *Low* confidence per stretch and hour.

## Quick Start & Demo
To launch the interactive journey planner:
```bash
cd crowd-planner
python app.py
```
Then open **`http://localhost:5000`** in your browser.

- Select Origin and Destination stops (e.g. `Badarpur Border (T)` to `Kapashera Border`).
- Set Departure time (e.g. `09:00`) and Day Type (`weekday` or `weekend`).
- Toggle between **Fastest** and **Most Comfortable** to see how route choices adapt.

## Outputs (`out/`)
- `crowding_by_stretch.csv`: Mean and p80 load, observed trips, crowding level, and confidence rating per route, stretch, day type, and hour.
- `crowding_by_route_hour.csv`: Operator-level view of peak bottleneck stretches by hour.
- `qa_checks.json`: Grounded statistical validations against known travel patterns.

## Delhi Transport Stack (GNCTD) API Integration
This prototype is architected to integrate directly with the official **Delhi Transport Stack Multimodal Journey Planner API**:
- **Endpoint**: `https://delhi.transportstack.in/api/serviceset/journey-planner/multi_modal`
- **Plug-and-play Auth**: Set your access token as an environment variable: `export DTS_API_KEY="<your-api-key>"` (or `$env:DTS_API_KEY="..."`).
- **Resilient Fallback**: If the external API key is pending approval or offline, the journey planner automatically uses our local precomputed routing graph grounded in the 2.56M ticket logs.

## Method (short; see TECHNICAL_NOTE.md)
Group tickets into bus trips (same route + vehicle, new trip after a 20-minute quiet gap), keep a
running count of boardings minus alightings per stretch, multiply by an assumed uplift for
untracked riders, and map load to Seats available / Standing room / Crowded.

## Limitations
Direct routes only; no waiting time or transfers; travel time from schedule offsets, not live
traffic; thresholds, seat count and the pass-holder uplift are assumptions to calibrate.

## Credits
Open-source libraries: pandas, NumPy, Flask. Data: Delhi Transport Stack (JICA / Chartr / CSM IIIT Delhi / ARF IIT Kanpur). All code written by the team during the hackathon.
