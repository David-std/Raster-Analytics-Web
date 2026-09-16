"""Attribute profiling for versioned geospatial source snapshots."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AttributeValueCount:
    value: str
    count: int


@dataclass(frozen=True)
class AttributeFieldProfile:
    field: str
    feature_count: int
    present_count: int
    missing_property_count: int
    null_or_blank_count: int
    non_null_count: int
    distinct_non_null_count: int
    top_values: list[AttributeValueCount]


@dataclass(frozen=True)
class GeoJSONAttributeProfile:
    source: str
    feature_count: int
    fields: list[AttributeFieldProfile]


def _normalized_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def profile_geojson_attributes(
    path: str | Path,
    *,
    fields: list[str],
    top_n: int = 25,
) -> GeoJSONAttributeProfile:
    """Profile selected properties without inventing values for absent or blank fields."""
    if not fields or any(not field.strip() for field in fields):
        raise ValueError("attribute profiling requires non-empty field names")
    if top_n <= 0:
        raise ValueError("top_n must be positive")

    source_path = Path(path)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("GeoJSON source must contain a features array")

    field_profiles: list[AttributeFieldProfile] = []
    for field in fields:
        counter: Counter[str] = Counter()
        present_count = 0
        missing_count = 0
        null_or_blank_count = 0

        for feature in features:
            if not isinstance(feature, dict):
                missing_count += 1
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict) or field not in properties:
                missing_count += 1
                continue
            present_count += 1
            normalized = _normalized_value(properties[field])
            if normalized is None:
                null_or_blank_count += 1
                continue
            counter[normalized] += 1

        top_values = [
            AttributeValueCount(value=value, count=count)
            for value, count in sorted(
                counter.items(),
                key=lambda item: (-item[1], item[0]),
            )[:top_n]
        ]
        field_profiles.append(
            AttributeFieldProfile(
                field=field,
                feature_count=len(features),
                present_count=present_count,
                missing_property_count=missing_count,
                null_or_blank_count=null_or_blank_count,
                non_null_count=sum(counter.values()),
                distinct_non_null_count=len(counter),
                top_values=top_values,
            )
        )

    return GeoJSONAttributeProfile(
        source=str(source_path),
        feature_count=len(features),
        fields=field_profiles,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profile selected properties from a GeoJSON source snapshot."
    )
    parser.add_argument("source", help="GeoJSON source snapshot")
    parser.add_argument("--fields", required=True, help="Comma-separated property names")
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--output", required=True, help="Output JSON path")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    fields = [field.strip() for field in args.fields.split(",") if field.strip()]
    profile = profile_geojson_attributes(args.source, fields=fields, top_n=args.top_n)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(asdict(profile), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
