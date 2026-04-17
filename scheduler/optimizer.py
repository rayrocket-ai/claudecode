"""Route optimizer + schedule builder for showing tours.

Two-stage pipeline:
  1. Optimize the order of stops using nearest-neighbor TSP
     (greedy, good enough for < 30 stops)
  2. Build a time-aware schedule with drive times, showing durations,
     and buffers between stops

The caller provides a starting point, a list of property addresses,
and a time window. We return a list of ScheduledStop objects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from scheduler.geocoder import GeoPoint

logger = logging.getLogger(__name__)

DEFAULT_SHOWING_MINUTES = 25
DEFAULT_BUFFER_MINUTES = 5


@dataclass
class ScheduledStop:
    """A single showing slot in a tour."""
    stop_number: int
    point: GeoPoint
    arrival_time: datetime
    departure_time: datetime
    drive_minutes_from_previous: int
    showing_minutes: int

    @property
    def address(self) -> str:
        return self.point.formatted_address

    def time_range_str(self) -> str:
        """Human-readable time range, e.g. '10:00 AM – 10:25 AM'."""
        fmt = "%-I:%M %p"
        try:
            return (
                f"{self.arrival_time.strftime(fmt)} – "
                f"{self.departure_time.strftime(fmt)}"
            )
        except ValueError:
            # Fallback for Windows where %-I doesn't work
            return (
                f"{self.arrival_time.strftime('%I:%M %p').lstrip('0')} – "
                f"{self.departure_time.strftime('%I:%M %p').lstrip('0')}"
            )


@dataclass
class Tour:
    """A fully scheduled tour."""
    start_point: GeoPoint
    stops: list[ScheduledStop] = field(default_factory=list)
    skipped_addresses: list[str] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total tour duration including drive back? No — from first arrival to last departure."""
        if not self.stops:
            return 0
        return int(
            (self.stops[-1].departure_time - self.stops[0].arrival_time).total_seconds()
            / 60
        )


def optimize_order(
    start: GeoPoint,
    stops: list[GeoPoint],
    matrix: list[list[int]],
) -> list[int]:
    """Nearest-neighbor TSP from the start point.

    The matrix must include `start` at index 0 and the `stops` at
    indices 1..n. Returns the 0-indexed order of the STOPS only
    (not including the start).
    """
    n = len(stops)
    if n == 0:
        return []

    unvisited = set(range(1, n + 1))  # 1..n indices into the combined matrix
    order: list[int] = []
    current = 0  # start point

    while unvisited:
        best = min(unvisited, key=lambda j: matrix[current][j])
        order.append(best - 1)  # convert back to stops-only index
        unvisited.remove(best)
        current = best

    return order


def build_schedule(
    start: GeoPoint,
    stops: list[GeoPoint],
    matrix: list[list[int]],
    earliest: datetime,
    latest: datetime,
    showing_minutes: int = DEFAULT_SHOWING_MINUTES,
    buffer_minutes: int = DEFAULT_BUFFER_MINUTES,
) -> Tour:
    """Build an optimized tour schedule.

    Args:
        start: Starting location (geocoded).
        stops: List of properties to tour (geocoded).
        matrix: Distance matrix where index 0 = start, 1..n = stops.
        earliest: Earliest start time.
        latest: Latest end time (tour must finish by this time).
        showing_minutes: Duration of each showing.
        buffer_minutes: Buffer between stops on top of drive time.

    Returns:
        Tour with ordered stops and any that were skipped (couldn't fit).
    """
    order = optimize_order(start, stops, matrix)

    tour = Tour(start_point=start)
    current_time = earliest
    previous_matrix_idx = 0  # start is at index 0

    for position, stop_idx in enumerate(order):
        stop = stops[stop_idx]
        matrix_idx = stop_idx + 1  # +1 because start is at index 0

        drive_min = matrix[previous_matrix_idx][matrix_idx]

        # Skip if no route available
        if drive_min >= 9999:
            logger.warning(
                "optimizer.unreachable",
                address=stop.formatted_address,
            )
            tour.skipped_addresses.append(stop.formatted_address)
            continue

        arrival = current_time + timedelta(minutes=drive_min + buffer_minutes)
        departure = arrival + timedelta(minutes=showing_minutes)

        # Check if it fits in the time window
        if departure > latest:
            logger.info(
                "optimizer.out_of_window",
                address=stop.formatted_address,
                would_end=departure.isoformat(),
                latest=latest.isoformat(),
            )
            tour.skipped_addresses.append(stop.formatted_address)
            continue

        tour.stops.append(
            ScheduledStop(
                stop_number=len(tour.stops) + 1,
                point=stop,
                arrival_time=arrival,
                departure_time=departure,
                drive_minutes_from_previous=drive_min,
                showing_minutes=showing_minutes,
            )
        )
        current_time = departure
        previous_matrix_idx = matrix_idx

    return tour
