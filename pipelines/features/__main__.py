from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pipelines.features.coverage import (
    SourceCoverageSemantics,
    build_district_units,
    build_grid_units,
    profile_source_coverage,
)
from pipelines.representation.spatial import (
    build_grid_definition,
    load_district_boundaries,
    projected_boundary_union,
)
from pipelines.representation.support import load_support_mask


def _load_config(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("feature coverage config must contain a sources array")
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure candidate feature geometry coverage by analytical representation."
    )
    parser.add_argument("boundary", help="Lima district boundary GeoJSON.")
    parser.add_argument("--config", required=True, help="Feature coverage source config JSON.")
    parser.add_argument("--source-dir", required=True, help="Directory containing source snapshots.")
    parser.add_argument("--output", required=True, help="Coverage report JSON path.")
    parser.add_argument("--grid-sizes", default="500,1000,2000")
    parser.add_argument("--support", help="Optional structural support GeoJSON.")
    parser.add_argument("--support-district-field", default="distrito")
    parser.add_argument("--support-source-crs", default="EPSG:32718")
    parser.add_argument("--support-year-field", default="Anio")
    return parser


def _parse_sizes(raw: str) -> list[int]:
    sizes = [int(value.strip()) for value in raw.split(",") if value.strip()]
    if not sizes or any(size <= 0 for size in sizes):
        raise ValueError("grid sizes must contain positive integers")
    return sizes


def main() -> None:
    args = _build_parser().parse_args()
    config = _load_config(args.config)
    source_dir = Path(args.source_dir)

    districts = load_district_boundaries(args.boundary)
    expected_districts = {district.name for district in districts}
    boundary = projected_boundary_union(districts)

    support = None
    if args.support:
        support = load_support_mask(
            args.support,
            expected_districts=expected_districts,
            district_field=args.support_district_field,
            support_label="zoning_support",
            source_crs=args.support_source_crs,
            year_field=args.support_year_field,
        )

    representations: dict[str, Any] = {
        "district": build_district_units(districts),
    }
    for size in _parse_sizes(args.grid_sizes):
        base = build_grid_definition(boundary, size)
        representations[base.representation_id] = build_grid_units(base)
        if support is not None:
            supported = build_grid_definition(
                boundary,
                size,
                support_predicate=support.intersects,
                support_label=support.profile.support_label,
            )
            representations[supported.representation_id] = build_grid_units(supported)

    reports: list[dict[str, Any]] = []
    for raw_source in config["sources"]:
        if not isinstance(raw_source, dict):
            raise ValueError("coverage source definitions must be JSON objects")
        source_id = str(raw_source["source_id"])
        feature_id = str(raw_source["feature_id"])
        filename = str(raw_source["file"])
        source_crs = str(raw_source.get("source_crs", "EPSG:32718"))
        semantics = SourceCoverageSemantics(raw_source.get("coverage_semantics", "unresolved"))
        source_path = source_dir / filename
        if not source_path.exists():
            raise FileNotFoundError(f"missing source snapshot for {source_id}: {source_path}")

        for representation_id, units in representations.items():
            report = profile_source_coverage(
                source_id=source_id,
                feature_id=feature_id,
                representation_id=representation_id,
                units=units,
                source_path=source_path,
                source_crs=source_crs,
                coverage_semantics=semantics,
            )
            reports.append(report.to_dict())

    output = {
        "selection_status": "FEATURE_COVERAGE_EVIDENCE_ONLY",
        "absence_rule": (
            "No observed source geometry is not numeric zero unless coverage_semantics is complete."
        ),
        "representations": {
            name: {"unit_count": len(units)} for name, units in representations.items()
        },
        "support_mask": vars(support.profile) if support is not None else None,
        "reports": reports,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
