from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from pyproj import Transformer

from pipelines.representation.spatial import (
    GridDefinition,
    assign_point_to_district,
    assign_point_to_grid,
    build_grid_definition,
    district_geometry_summary,
    load_district_boundaries,
    normalize_name,
    projected_boundary_union,
)
from pipelines.representation.support import SupportMask, load_support_mask
from pipelines.representation.temporal import (
    enumerate_period_ids,
    parse_event_datetime,
    period_id,
)


@dataclass(frozen=True)
class Event:
    event_id: str
    moment: datetime
    longitude: float
    latitude: float
    source_district: str
    crash_class: str

    @property
    def strict_atropello(self) -> bool:
        return "ATROPELLO" in normalize_name(self.crash_class)


@dataclass(frozen=True)
class AnalysisWindow:
    window_id: str
    start: date
    end: date
    role: str
    note: str


@dataclass(frozen=True)
class SpatialCandidate:
    representation_id: str
    kind: str
    unit_count: int
    assignments: tuple[str | None, ...]
    metadata: dict[str, Any]


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def load_events(csv_path: str | Path) -> list[Event]:
    events: list[Event] = []
    with Path(csv_path).open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            moment = parse_event_datetime(
                str(row.get("crash_date") or ""),
                str(row.get("crash_time") or ""),
            )
            longitude = _float(row.get("longitude"))
            latitude = _float(row.get("latitude"))
            if moment is None or longitude is None or latitude is None:
                continue
            events.append(
                Event(
                    event_id=str(row.get("crash_id") or "").strip(),
                    moment=moment,
                    longitude=longitude,
                    latitude=latitude,
                    source_district=normalize_name(row.get("district")),
                    crash_class=str(row.get("crash_class") or "").strip(),
                )
            )
    if not events:
        raise ValueError("No events with valid date and coordinates were loaded")
    events.sort(key=lambda event: (event.moment, event.event_id))
    return events


def _population_indexes(events: list[Event], population: str) -> list[int]:
    if population == "pedestrian_linked_fatal":
        return list(range(len(events)))
    if population == "strict_fatal_atropello":
        return [index for index, event in enumerate(events) if event.strict_atropello]
    raise ValueError(f"Unknown outcome population: {population}")


def _nearest_rank_quantile(
    total_count: int,
    zero_count: int,
    positive_values: Counter[int],
    quantile: float,
) -> int:
    if total_count <= 0:
        return 0
    rank = max(1, math.ceil(quantile * total_count))
    if rank <= zero_count:
        return 0
    cursor = zero_count
    for value in sorted(positive_values):
        cursor += positive_values[value]
        if rank <= cursor:
            return value
    return max(positive_values, default=0)


def _distribution_metrics(
    pair_counts: Counter[tuple[str, str]],
    total_cells: int,
    assigned_events: int,
) -> dict[str, Any]:
    occupied_cells = len(pair_counts)
    zero_cells = max(0, total_cells - occupied_cells)
    frequency = Counter(pair_counts.values())
    return {
        "occupied_unit_period_cells": occupied_cells,
        "zero_event_cells": zero_cells,
        "zero_event_ratio": round(zero_cells / total_cells, 6) if total_cells else None,
        "events_per_cell_mean": round(assigned_events / total_cells, 8) if total_cells else None,
        "events_per_cell_p50": _nearest_rank_quantile(total_cells, zero_cells, frequency, 0.50),
        "events_per_cell_p90": _nearest_rank_quantile(total_cells, zero_cells, frequency, 0.90),
        "events_per_cell_p95": _nearest_rank_quantile(total_cells, zero_cells, frequency, 0.95),
        "events_per_cell_p99": _nearest_rank_quantile(total_cells, zero_cells, frequency, 0.99),
        "events_per_cell_max": max(pair_counts.values(), default=0),
        "events_per_nonzero_cell_mean": (
            round(mean(pair_counts.values()), 6) if pair_counts else None
        ),
    }


def _district_candidate(events: list[Event], districts) -> tuple[SpatialCandidate, dict[str, Any]]:
    assignments: list[str | None] = []
    mismatches: Counter[str] = Counter()
    assigned = 0
    for event in events:
        unit_id = assign_point_to_district(event.longitude, event.latitude, districts)
        assignments.append(unit_id)
        if unit_id is None:
            continue
        assigned += 1
        geometry_name = unit_id.removeprefix("district:")
        if event.source_district and event.source_district != geometry_name:
            mismatches[f"{event.source_district} -> {geometry_name}"] += 1

    audit = {
        "events_checked": len(events),
        "assigned_to_boundary": assigned,
        "unassigned_to_boundary": len(events) - assigned,
        "source_district_geometry_mismatches": sum(mismatches.values()),
        "mismatch_pairs": dict(mismatches.most_common()),
    }
    return (
        SpatialCandidate(
            representation_id="district",
            kind="district",
            unit_count=len(districts),
            assignments=tuple(assignments),
            metadata={"district_count": len(districts), "support_label": None},
        ),
        audit,
    )


def _candidate_from_grid(
    events: list[Event],
    grid: GridDefinition,
    projection: Transformer,
) -> SpatialCandidate:
    assignments = tuple(
        assign_point_to_grid(
            event.longitude,
            event.latitude,
            grid,
            transformer=projection,
        )
        for event in events
    )
    assigned = sum(unit_id is not None for unit_id in assignments)
    return SpatialCandidate(
        representation_id=grid.representation_id,
        kind="regular_grid",
        unit_count=grid.unit_count,
        assignments=assignments,
        metadata={
            "cell_size_m": grid.cell_size_m,
            "offset_fraction": grid.offset_fraction,
            "origin_x": round(grid.origin_x, 3),
            "origin_y": round(grid.origin_y, 3),
            "support_label": grid.support_label,
            "full_cell_count": grid.full_cell_count,
            "partial_cell_count": grid.partial_cell_count,
            "boundary_intersecting_cell_count": grid.boundary_intersecting_cell_count,
            "excluded_by_support_count": grid.excluded_by_support_count,
            "retained_cell_ratio_of_boundary_grid": round(
                grid.unit_count / grid.boundary_intersecting_cell_count,
                6,
            ),
            "all_event_assignment_ratio": round(assigned / len(events), 6),
            "boundary_area_km2": round(grid.boundary_area_km2, 3),
        },
    )


def _grid_candidates(
    events: list[Event],
    boundary_projected,
    grid_sizes: tuple[int, ...],
    support_mask: SupportMask | None,
) -> list[SpatialCandidate]:
    projection = Transformer.from_crs("EPSG:4326", "EPSG:32718", always_xy=True)
    candidates: list[SpatialCandidate] = []
    for cell_size in grid_sizes:
        for offset_fraction in (0.0, 0.5):
            full_grid = build_grid_definition(
                boundary_projected,
                cell_size,
                offset_fraction=offset_fraction,
            )
            candidates.append(_candidate_from_grid(events, full_grid, projection))

            if support_mask is not None:
                masked_grid = build_grid_definition(
                    boundary_projected,
                    cell_size,
                    offset_fraction=offset_fraction,
                    support_predicate=support_mask.intersects,
                    support_label=support_mask.profile.support_label,
                )
                candidates.append(_candidate_from_grid(events, masked_grid, projection))
    return candidates


def _windows(events: list[Event]) -> list[AnalysisWindow]:
    observed_start = min(event.moment.date() for event in events)
    observed_end = max(event.moment.date() for event in events)
    windows = [
        AnalysisWindow(
            window_id="complete_calendar_years_2021_2024",
            start=date(2021, 1, 1),
            end=date(2024, 12, 31),
            role="PRIMARY_REPRESENTATION_DIAGNOSTIC",
            note="Excludes the known partial 2025 source interval from like-for-like year coverage.",
        )
    ]
    if observed_end > date(2024, 12, 31):
        windows.append(
            AnalysisWindow(
                window_id="observed_source_cutoff",
                start=observed_start,
                end=observed_end,
                role="SOURCE_CUTOFF_SENSITIVITY",
                note=(
                    "Ends at the current source cutoff and must not be interpreted as a complete "
                    "final calendar year."
                ),
            )
        )
    return windows


def _result_for(
    events: list[Event],
    event_indexes: list[int],
    spatial: SpatialCandidate,
    temporal_kind: str,
    window: AnalysisWindow,
    population: str,
) -> dict[str, Any]:
    periods = enumerate_period_ids(window.start, window.end, temporal_kind)
    period_set = set(periods)
    pair_counts: Counter[tuple[str, str]] = Counter()
    spatial_with_event: set[str] = set()
    periods_with_event: set[str] = set()
    assigned_events = 0
    unassigned_events = 0

    for index in event_indexes:
        event = events[index]
        if not (window.start <= event.moment.date() <= window.end):
            continue
        unit_id = spatial.assignments[index]
        if unit_id is None:
            unassigned_events += 1
            continue
        bucket = period_id(event.moment, temporal_kind)
        if bucket not in period_set:
            continue
        pair_counts[(unit_id, bucket)] += 1
        spatial_with_event.add(unit_id)
        periods_with_event.add(bucket)
        assigned_events += 1

    total_cells = spatial.unit_count * len(periods)
    metrics = _distribution_metrics(pair_counts, total_cells, assigned_events)
    denominator = assigned_events + unassigned_events
    return {
        "window_id": window.window_id,
        "window_role": window.role,
        "population": population,
        "spatial_representation": spatial.representation_id,
        "spatial_kind": spatial.kind,
        "spatial_metadata": spatial.metadata,
        "temporal_representation": temporal_kind,
        "spatial_units": spatial.unit_count,
        "periods": len(periods),
        "unit_period_cells": total_cells,
        "assigned_events": assigned_events,
        "unassigned_events": unassigned_events,
        "event_assignment_ratio": (
            round(assigned_events / denominator, 6) if denominator else None
        ),
        "spatial_units_with_event": len(spatial_with_event),
        "spatial_unit_activity_ratio": (
            round(len(spatial_with_event) / spatial.unit_count, 6)
            if spatial.unit_count
            else None
        ),
        "periods_with_event": len(periods_with_event),
        "period_activity_ratio": (
            round(len(periods_with_event) / len(periods), 6) if periods else None
        ),
        **metrics,
    }


def _boundary_sensitivity(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed: dict[tuple[str, str, str, int, str, float], dict[str, Any]] = {}
    for result in results:
        metadata = result["spatial_metadata"]
        if result["spatial_kind"] != "regular_grid":
            continue
        cell_size = metadata.get("cell_size_m")
        offset = metadata.get("offset_fraction")
        support_label = metadata.get("support_label") or "full_boundary"
        if not isinstance(cell_size, int) or not isinstance(offset, (int, float)):
            continue
        key = (
            result["window_id"],
            result["population"],
            result["temporal_representation"],
            cell_size,
            str(support_label),
            float(offset),
        )
        indexed[key] = result

    comparisons: list[dict[str, Any]] = []
    prefixes = sorted({key[:5] for key in indexed})
    for prefix in prefixes:
        base = indexed.get((*prefix, 0.0))
        shifted = indexed.get((*prefix, 0.5))
        if base is None or shifted is None:
            continue
        comparisons.append(
            {
                "window_id": prefix[0],
                "population": prefix[1],
                "temporal_representation": prefix[2],
                "cell_size_m": prefix[3],
                "support_label": prefix[4],
                "unit_count_delta_half_shift_minus_base": (
                    shifted["spatial_units"] - base["spatial_units"]
                ),
                "zero_event_ratio_delta": round(
                    shifted["zero_event_ratio"] - base["zero_event_ratio"],
                    6,
                ),
                "assigned_event_delta": shifted["assigned_events"] - base["assigned_events"],
                "occupied_cell_delta": (
                    shifted["occupied_unit_period_cells"]
                    - base["occupied_unit_period_cells"]
                ),
                "max_events_per_cell_delta": (
                    shifted["events_per_cell_max"] - base["events_per_cell_max"]
                ),
            }
        )
    return comparisons


def run_representation_experiment(
    event_csv: str | Path,
    boundary_geojson: str | Path,
    *,
    grid_sizes: tuple[int, ...] = (250, 500, 1000, 2000),
    temporal_kinds: tuple[str, ...] = ("month", "iso_week", "day", "daypart_6h"),
    district_field: str = "NOMBDIST",
    province_field: str | None = "NOMBPROV",
    support_geojson: str | Path | None = None,
    support_label: str = "zoning_support",
    support_district_field: str = "distrito",
    support_source_crs: str = "EPSG:32718",
    support_year_field: str | None = "Anio",
) -> dict[str, Any]:
    """Measure spatial-temporal candidates without selecting one prematurely."""
    events = load_events(event_csv)
    districts = load_district_boundaries(
        boundary_geojson,
        district_field=district_field,
        province_field=province_field,
    )
    expected_districts = {district.name for district in districts}
    boundary_projected = projected_boundary_union(districts)

    support_mask = None
    if support_geojson is not None:
        support_mask = load_support_mask(
            support_geojson,
            expected_districts=expected_districts,
            district_field=support_district_field,
            support_label=support_label,
            source_crs=support_source_crs,
            year_field=support_year_field,
        )

    district_candidate, district_audit = _district_candidate(events, districts)
    spatial_candidates = [district_candidate]
    spatial_candidates.extend(
        _grid_candidates(events, boundary_projected, grid_sizes, support_mask)
    )

    populations = ("pedestrian_linked_fatal", "strict_fatal_atropello")
    indexes_by_population = {
        population: _population_indexes(events, population) for population in populations
    }

    results: list[dict[str, Any]] = []
    windows = _windows(events)
    for window in windows:
        for population in populations:
            event_indexes = indexes_by_population[population]
            for spatial in spatial_candidates:
                for temporal_kind in temporal_kinds:
                    results.append(
                        _result_for(
                            events,
                            event_indexes,
                            spatial,
                            temporal_kind,
                            window,
                            population,
                        )
                    )

    return {
        "selection_status": "NOT_SELECTED",
        "selection_reason": (
            "P2 measures sparsity, event assignment, source support and boundary sensitivity "
            "before a spatial or temporal representation is frozen."
        ),
        "event_source": str(event_csv),
        "boundary_source": str(boundary_geojson),
        "event_count_loaded": len(events),
        "strict_atropello_count_loaded": sum(event.strict_atropello for event in events),
        "outcome_populations": {
            "pedestrian_linked_fatal": (
                "Fatal crash linked to at least one person classified as PEATON."
            ),
            "strict_fatal_atropello": (
                "Pedestrian-linked fatal crash whose recorded crash class contains ATROPELLO."
            ),
        },
        "boundary": district_geometry_summary(districts),
        "district_assignment_audit": district_audit,
        "support_mask": asdict(support_mask.profile) if support_mask is not None else None,
        "support_interpretation": (
            "A support mask only limits where a structural source proves mapped urban support; "
            "it is not pedestrian exposure, a risk denominator, or a final spatial-unit choice."
            if support_mask is not None
            else None
        ),
        "analysis_windows": [
            {
                **asdict(window),
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
            }
            for window in windows
        ],
        "spatial_candidates": [
            {
                "representation_id": candidate.representation_id,
                "kind": candidate.kind,
                "unit_count": candidate.unit_count,
                "metadata": candidate.metadata,
            }
            for candidate in spatial_candidates
        ],
        "temporal_candidates": list(temporal_kinds),
        "blocked_spatial_candidates": [
            {
                "kind": "road_segment",
                "state": "BLOCKED",
                "reason": (
                    "No complete, qualified Lima urban road network with stable segment identity "
                    "has yet been accepted."
                ),
            },
            {
                "kind": "intersection_node",
                "state": "BLOCKED",
                "reason": (
                    "The qualified signalized-intersection layer is not equivalent to a complete "
                    "street-intersection topology."
                ),
            },
        ],
        "results": results,
        "grid_boundary_sensitivity": _boundary_sensitivity(results),
    }
