# Proposal: Crowd-aware Bus Planner (Problem 2)

**Team:** <TEAM NAME>: <MEMBERS>

## Problem relevance
Journey planners rank bus options by time and changes only, yet a packed bus is slow to board,
hard to stand in, and often skipped by those who can choose. Delhi records every ticket, so the
data to estimate crowding already exists. Commuters can pick a trip they can bear; operators can
see which routes and hours are overloaded.

## Approach
Rebuild each bus trip from ETM and e-ticketing records (route + vehicle + time gap), keep a running
count of boardings minus alightings per stretch, adjust for riders without tickets, and map load
to three levels a commuter reads in a second: Seats available, Standing room, Crowded. Aggregate
by route, direction, stretch, day type and hour, with a confidence rating from the number of
observed trips. The planner lists direct options with travel time and crowding, and also the same
bus 20 and 40 minutes later, sortable by Fastest or Most comfortable.

## Data
Official October 2026 ticket file (about 2.56M tickets) and static GTFS for stop order and
schedule offsets. The prototype is verified on a synthetic sample with the same schema.

## Feasibility and plan
The pipeline is a rerunnable script. Next steps for Phase 2: run on the full month, derive stop order and times from GTFS, calibrate the untracked-rider uplift and seat capacities by bus type, add transfers, and validate week-to-week stability and known corridors.

## Impact
Spreads load across departures for commuters; gives operators a ranked list of overloaded stretches and hours to target extra buses.
