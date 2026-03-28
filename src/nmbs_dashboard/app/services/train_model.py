"""Build a train-centric index from endpoint snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .snapshot_loader import unwrap_endpoint_body


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _split_stop_id(stop_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not stop_id:
        return None, None
    if "_" in stop_id:
        base, platform = stop_id.rsplit("_", 1)
        return base, platform
    return stop_id, None


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derive_trip_number(train: Dict[str, Any]) -> Optional[str]:
    trip = train.get("trip", {})
    for key in ("trip_number", "trip_short_name"):
        val = trip.get(key)
        if val not in (None, ""):
            return str(val)

    trip_id = str(train.get("trip_id", ""))
    parts = trip_id.split(":")
    if len(parts) >= 2 and parts[-2]:
        return parts[-2]

    return None


def _infer_position(train: Dict[str, Any]) -> Dict[str, Any]:
    trajectories = train.get("trajectory_updates", [])
    if trajectories:
        latest = trajectories[-1]
        stops = latest.get("stops", [])
        if not stops:
            return {"status": "No stop information"}

        now_epoch = int(datetime.now(timezone.utc).timestamp())
        current_idx = 0
        for idx, stop in enumerate(stops):
            checkpoint = _to_int(stop.get("departure_timestamp"), 0) or _to_int(stop.get("arrival_timestamp"), 0)
            if checkpoint and checkpoint <= now_epoch:
                current_idx = idx

        current_stop = stops[current_idx]
        next_stop = stops[current_idx + 1] if current_idx + 1 < len(stops) else None

        lat = current_stop.get("lat")
        lon = current_stop.get("lon")

        if next_stop and lat is not None and lon is not None:
            dep_ts = _to_int(current_stop.get("departure_timestamp"), 0)
            arr_ts = _to_int(next_stop.get("arrival_timestamp"), 0)
            if dep_ts and arr_ts and dep_ts < now_epoch < arr_ts:
                progress = (now_epoch - dep_ts) / (arr_ts - dep_ts)
                next_lat = next_stop.get("lat")
                next_lon = next_stop.get("lon")
                if next_lat is not None and next_lon is not None:
                    lat = lat + progress * (next_lat - lat)
                    lon = lon + progress * (next_lon - lon)

        return {
            "status": "in transit" if next_stop else "arrived",
            "current_station": current_stop.get("station_name"),
            "next_station": next_stop.get("station_name") if next_stop else None,
            "lat": lat,
            "lon": lon,
            "snapshot_id": latest.get("snapshot_id"),
            "observed_at": latest.get("observed_at"),
            "delay_minutes": round(_to_int(current_stop.get("delay_seconds"), 0) / 60, 2),
        }

    realtime = train.get("realtime_updates", [])
    if realtime:
        latest = realtime[-1]
        updates = latest.get("stop_updates", [])
        first = updates[0] if updates else {}
        return {
            "status": "realtime update",
            "current_station": train.get("known_stops", {}).get(first.get("base_stop_id")),
            "next_station": None,
            "lat": None,
            "lon": None,
            "snapshot_id": latest.get("snapshot_id"),
            "observed_at": latest.get("observed_at"),
            "delay_minutes": round(_to_int(latest.get("max_delay_seconds"), 0) / 60, 2),
        }

    return {"status": "No observations"}


def _ensure_train(trains: Dict[str, Dict[str, Any]], trip_id: str) -> Dict[str, Any]:
    if trip_id not in trains:
        trains[trip_id] = {
            "trip_id": trip_id,
            "entity_ids": set(),
            "route": {},
            "trip": {},
            "realtime_updates": [],
            "trajectory_updates": [],
            "delay_history": [],
            "platform_changes": [],
            "skipped_stops": [],
            "known_stops": {},
            "_platform_history": {},
        }
    return trains[trip_id]


def build_train_index(repository: Dict[str, Any]) -> Dict[str, Any]:
    trains: Dict[str, Dict[str, Any]] = {}

    for snapshot in repository.get("snapshots", []):
        snapshot_id = str(snapshot.get("id"))
        observed_at = snapshot.get("exported_at") or snapshot_id
        endpoints = snapshot.get("endpoints", {})

        realtime_payload = endpoints.get("realtime", {}).get("payload")
        realtime_body = unwrap_endpoint_body(realtime_payload)
        entities = realtime_body.get("entity", []) if isinstance(realtime_body, dict) else []

        for entity in entities:
            trip_update = entity.get("tripUpdate", {})
            trip = trip_update.get("trip", {})
            trip_id = trip.get("tripId") or trip.get("trip_id") or entity.get("id")
            if not trip_id:
                continue

            train = _ensure_train(trains, str(trip_id))
            entity_id = entity.get("id")
            if entity_id:
                train["entity_ids"].add(str(entity_id))

            if not train.get("trip"):
                train["trip"] = {
                    "trip_id": trip.get("tripId") or trip.get("trip_id"),
                    "start_time": trip.get("startTime") or trip.get("start_time"),
                    "start_date": trip.get("startDate") or trip.get("start_date"),
                }

            max_delay_seconds = 0
            stop_updates: List[Dict[str, Any]] = []

            for stop in trip_update.get("stopTimeUpdate", []):
                stop_id = stop.get("stopId") or stop.get("stop_id")
                base_stop_id, platform = _split_stop_id(stop_id)

                arrival = stop.get("arrival") or {}
                departure = stop.get("departure") or {}
                arr_delay = _to_int(arrival.get("delay"), 0)
                dep_delay = _to_int(departure.get("delay"), 0)
                delay_seconds = max(arr_delay, dep_delay)
                max_delay_seconds = max(max_delay_seconds, delay_seconds)

                rel = stop.get("scheduleRelationship") or stop.get("schedule_relationship")
                if rel == "SKIPPED":
                    train["skipped_stops"].append(
                        {
                            "snapshot_id": snapshot_id,
                            "observed_at": observed_at,
                            "stop_id": stop_id,
                            "base_stop_id": base_stop_id,
                        }
                    )

                if base_stop_id:
                    platform_history = train["_platform_history"].setdefault(base_stop_id, set())
                    if platform and platform_history and platform not in platform_history:
                        previous = sorted(platform_history)[-1]
                        train["platform_changes"].append(
                            {
                                "snapshot_id": snapshot_id,
                                "observed_at": observed_at,
                                "base_stop_id": base_stop_id,
                                "old_platform": previous,
                                "new_platform": platform,
                            }
                        )
                    if platform:
                        platform_history.add(platform)

                stop_updates.append(
                    {
                        "stop_id": stop_id,
                        "base_stop_id": base_stop_id,
                        "platform": platform,
                        "arrival_delay_seconds": arr_delay,
                        "departure_delay_seconds": dep_delay,
                        "delay_seconds": delay_seconds,
                        "arrival_time": arrival.get("time"),
                        "departure_time": departure.get("time"),
                        "schedule_relationship": rel,
                    }
                )

            train["realtime_updates"].append(
                {
                    "snapshot_id": snapshot_id,
                    "observed_at": observed_at,
                    "entity_id": entity_id,
                    "start_time": trip.get("startTime") or trip.get("start_time"),
                    "start_date": trip.get("startDate") or trip.get("start_date"),
                    "stop_updates": stop_updates,
                    "max_delay_seconds": max_delay_seconds,
                }
            )

            train["delay_history"].append(
                {
                    "snapshot_id": snapshot_id,
                    "observed_at": observed_at,
                    "source": "realtime",
                    "delay_minutes": round(max_delay_seconds / 60, 2),
                }
            )

        trajectories_payload = endpoints.get("trajectories", {}).get("payload")
        trajectories_body = unwrap_endpoint_body(trajectories_payload)
        trajectories = trajectories_body.get("data", []) if isinstance(trajectories_body, dict) else []

        for trajectory in trajectories:
            trip_id = trajectory.get("trip_id") or trajectory.get("entity_id")
            if not trip_id:
                continue

            train = _ensure_train(trains, str(trip_id))
            route = trajectory.get("route", {})
            if route:
                train["route"] = route

            trip_info = trajectory.get("trip", {})
            if trip_info:
                merged = dict(train.get("trip", {}))
                merged.update(trip_info)
                train["trip"] = merged

            processed_stops: List[Dict[str, Any]] = []
            max_delay_seconds = 0

            for stop in trajectory.get("stops", []):
                stop_id = stop.get("stop_id")
                base_stop_id, platform = _split_stop_id(stop_id)

                station = stop.get("station", {})
                location = station.get("location", {})
                lat = _to_float(location.get("latitude"))
                lon = _to_float(location.get("longitude"))

                station_name = station.get("name")
                if base_stop_id and station_name:
                    train["known_stops"][base_stop_id] = station_name

                arrival = stop.get("arrival") or {}
                departure = stop.get("departure") or {}
                arr_delay = _to_int(arrival.get("delay_seconds"), _to_int(arrival.get("delay"), 0))
                dep_delay = _to_int(departure.get("delay_seconds"), _to_int(departure.get("delay"), 0))
                delay_seconds = max(arr_delay, dep_delay)
                max_delay_seconds = max(max_delay_seconds, delay_seconds)

                processed_stops.append(
                    {
                        "stop_id": stop_id,
                        "base_stop_id": base_stop_id,
                        "platform": platform,
                        "station_name": station_name,
                        "lat": lat,
                        "lon": lon,
                        "arrival_datetime": arrival.get("datetime"),
                        "departure_datetime": departure.get("datetime"),
                        "arrival_timestamp": arrival.get("timestamp"),
                        "departure_timestamp": departure.get("timestamp"),
                        "delay_seconds": delay_seconds,
                        "status": departure.get("status") or arrival.get("status"),
                    }
                )

            train["trajectory_updates"].append(
                {
                    "snapshot_id": snapshot_id,
                    "observed_at": observed_at,
                    "route": route,
                    "trip": trip_info,
                    "stops": processed_stops,
                    "max_delay_seconds": max_delay_seconds,
                }
            )
            train["delay_history"].append(
                {
                    "snapshot_id": snapshot_id,
                    "observed_at": observed_at,
                    "source": "trajectories",
                    "delay_minutes": round(max_delay_seconds / 60, 2),
                }
            )

    finalized: Dict[str, Dict[str, Any]] = {}
    for trip_id, train in trains.items():
        train["realtime_updates"].sort(key=lambda item: item.get("observed_at") or "")
        train["trajectory_updates"].sort(key=lambda item: item.get("observed_at") or "")
        train["delay_history"].sort(key=lambda item: (item.get("observed_at") or "", item.get("source") or ""))
        train["platform_changes"].sort(key=lambda item: item.get("observed_at") or "")
        train["skipped_stops"].sort(key=lambda item: item.get("observed_at") or "")

        train["entity_ids"] = sorted(train["entity_ids"])
        train.pop("_platform_history", None)
        train["trip_number"] = _derive_trip_number(train)
        train["current_position"] = _infer_position(train)
        finalized[trip_id] = train

    train_options: List[Dict[str, str]] = []
    for trip_id, train in sorted(finalized.items()):
        route_name = train.get("route", {}).get("route_name") or train.get("trip", {}).get("trip_headsign")
        trip_number = train.get("trip_number")

        if trip_number and route_name:
            label = f"{trip_number} · {route_name}"
        elif route_name:
            label = str(route_name)
        elif trip_number:
            label = f"Train {trip_number}"
        else:
            label = trip_id

        train_options.append({"label": f"{label} ({trip_id})", "value": trip_id})

    trains_with_delay = sum(
        1 for train in finalized.values() if any(item.get("delay_minutes", 0) > 0 for item in train.get("delay_history", []))
    )
    trains_with_platform_changes = sum(1 for train in finalized.values() if train.get("platform_changes"))

    return {
        "trains": finalized,
        "train_options": train_options,
        "metrics": {
            "snapshot_count": repository.get("snapshot_count", 0),
            "endpoint_count_latest": len(repository.get("endpoint_names", [])),
            "train_count": len(finalized),
            "trains_with_delay": trains_with_delay,
            "trains_with_platform_changes": trains_with_platform_changes,
        },
    }
