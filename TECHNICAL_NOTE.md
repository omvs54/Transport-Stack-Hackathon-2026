# Technical note: crowding estimation from ticket data

**Goal.** Estimate people on board by route, direction, stretch, day type and hour from ETM and
e-ticketing records, and show it beside travel time in a planner.

## Pipeline
1. **Clean.** Parse `created_at`; map `start_stop_name` and `end_stop_name` to stop positions on the route (from GTFS-derived `routes_stops.csv`). Tickets whose stops are not on the route are dropped and counted.
2. **Alighting.** If the end stop is downstream of the start, use it. Otherwise (missing or invalid) impute the route's median ride length in stops.
3. **Trips.** Sort by route and vehicle; a gap above 20 minutes starts a new trip. Direction comes from the route suffix (UP/DN).
4. **Load.** Per trip, load on stretch k = sum of passengers with start <= k < end (difference array + cumulative sum). Trip start time = median of (ticket time minus scheduled minutes from the first stop), so each stretch gets its own clock time and hour bin.
5. **Untracked riders.** Pass holders and others do not appear. We multiply load by a single uplift (default 1.15, an assumption, `--uplift`).
6. **Aggregate.** Mean and 80th-percentile load per route, stretch, day type, hour; level = Seats available (<0.85 x seats), Standing room (<1.7 x seats), Crowded (above), with 35 assumed seats (`--seats`).
7. **Confidence.** high >= 20 observed trips, medium >= 8, else low; shown in the planner.

## Checks (`out/qa_checks.json`)
Peak vs midday load ratio, weekday vs weekend ratio, busiest hours and stretches, and agreement
between odd and even weeks as a stability test. On the synthetic sample these behave as built
in, which only proves the code works. **They must be re-read on the real data.**

## Where estimates are least reliable
- Low-ticket routes and off-peak hours (flagged low confidence).
- Riders without tickets: the uplift is one number for all routes; true pass share differs by corridor.
- Planned vs actual alighting: imputed ends and early/late exits blur the load by a stop or two.
- Trip segmentation by time gap can merge back-to-back trips or split a long one; GTFS trip IDs or GPS would be better.
- Trips with no tickets at all are invisible, which biases quiet hours upward.
- Bus size: a single seat count is assumed; the vehicle-type mapping is future work.
- One month of data: no seasons, festivals or monsoon.

## Planner limits
Direct routes only; no transfers or waiting time; travel time = scheduled offsets.
