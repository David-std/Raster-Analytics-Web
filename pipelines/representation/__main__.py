from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipelines.representation.experiment import run_representation_experiment


def _positive_int_list(value: str) -> tuple[int, ...]:
    items = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("Expected comma-separated positive integers")
    return items


def _string_list(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items:
        raise argparse.ArgumentTypeError("Expected at least one comma-separated value")
    return items


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure spatial-temporal representation sparsity and assignment quality."
    )
    parser.add_argument("events", type=Path)
    parser.add_argument("boundary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--grid-sizes", type=_positive_int_list, default=(250, 500, 1000, 2000))
    parser.add_argument(
        "--temporal-kinds",
        type=_string_list,
        default=("month", "iso_week", "day", "daypart_6h"),
    )
    parser.add_argument("--district-field", default="NOMBDIST")
    parser.add_argument("--province-field", default="NOMBPROV")
    parser.add_argument("--support", type=Path)
    parser.add_argument("--support-label", default="zoning_support")
    parser.add_argument("--support-district-field", default="distrito")
    parser.add_argument("--support-source-crs", default="EPSG:32718")
    parser.add_argument("--support-year-field", default="Anio")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    report = run_representation_experiment(
        args.events,
        args.boundary,
        grid_sizes=args.grid_sizes,
        temporal_kinds=args.temporal_kinds,
        district_field=args.district_field,
        province_field=args.province_field or None,
        support_geojson=args.support,
        support_label=args.support_label,
        support_district_field=args.support_district_field,
        support_source_crs=args.support_source_crs,
        support_year_field=args.support_year_field or None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Representation report written to {args.output}")


if __name__ == "__main__":
    main()
