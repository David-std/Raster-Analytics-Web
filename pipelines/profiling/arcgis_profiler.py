from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pipelines.profiling.source_catalog import load_source_catalog

_DEFAULT_DISTINCT_FIELDS = ("Anio", "Ciudad", "distrito")


@dataclass(frozen=True)
class ArcGISLayerProfile:
    source_id: str
    url: str
    name: str | None
    layer_type: str | None
    geometry_type: str | None
    feature_count: int | None
    max_record_count: int | None
    spatial_reference: int | str | None
    extent: dict[str, Any] | None
    wgs84_extent: dict[str, Any] | None
    fields: list[dict[str, Any]]
    distinct_values: dict[str, list[Any]]
    distinct_value_errors: dict[str, str]
    supported_query_formats: list[str]
    capabilities: str | None
    error: str | None = None


def _json_request(url: str, timeout: int) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Raster-Analytics-Web/source-profiler"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ArcGIS response must be a JSON object")
    if "error" in payload:
        raise ValueError(f"ArcGIS error: {payload['error']}")
    return payload


def _metadata_url(layer_url: str) -> str:
    return f"{layer_url.rstrip('/')}?{urlencode({'f': 'json'})}"


def _count_url(layer_url: str) -> str:
    params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    return f"{layer_url.rstrip('/')}/query?{urlencode(params)}"


def _extent_url(layer_url: str) -> str:
    params = {
        "where": "1=1",
        "returnExtentOnly": "true",
        "outSR": "4326",
        "f": "json",
    }
    return f"{layer_url.rstrip('/')}/query?{urlencode(params)}"


def _distinct_url(layer_url: str, field: str) -> str:
    params = {
        "where": "1=1",
        "outFields": field,
        "returnGeometry": "false",
        "returnDistinctValues": "true",
        "orderByFields": field,
        "resultRecordCount": "250",
        "f": "json",
    }
    return f"{layer_url.rstrip('/')}/query?{urlencode(params)}"


def _spatial_reference(metadata: dict[str, Any]) -> int | str | None:
    extent = metadata.get("extent")
    if not isinstance(extent, dict):
        return None
    spatial_reference = extent.get("spatialReference")
    if not isinstance(spatial_reference, dict):
        return None
    return spatial_reference.get("latestWkid") or spatial_reference.get("wkid")


def _query_distinct_values(
    layer_url: str,
    fields: tuple[str, ...],
    timeout: int,
) -> tuple[dict[str, list[Any]], dict[str, str]]:
    values: dict[str, list[Any]] = {}
    errors: dict[str, str] = {}
    for field in fields:
        try:
            payload = _json_request(_distinct_url(layer_url, field), timeout)
            features = payload.get("features")
            if not isinstance(features, list):
                raise ValueError("Distinct-value response does not contain a features array")
            distinct = []
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                attributes = feature.get("attributes")
                if isinstance(attributes, dict) and field in attributes:
                    distinct.append(attributes[field])
            values[field] = distinct
        except Exception as exc:
            errors[field] = f"{type(exc).__name__}: {exc}"
    return values, errors


def profile_arcgis_layer(
    source_id: str,
    layer_url: str,
    *,
    distinct_fields: tuple[str, ...] = (),
    timeout: int = 30,
) -> ArcGISLayerProfile:
    """Profile ArcGIS metadata, count, WGS84 extent, and selected coverage fields."""
    try:
        metadata = _json_request(_metadata_url(layer_url), timeout)
        count_payload = _json_request(_count_url(layer_url), timeout)
        feature_count = count_payload.get("count")

        wgs84_extent = None
        try:
            extent_payload = _json_request(_extent_url(layer_url), timeout)
            if isinstance(extent_payload.get("extent"), dict):
                wgs84_extent = extent_payload["extent"]
        except Exception:
            # Native metadata still remains useful when the server cannot project an extent.
            wgs84_extent = None

        raw_fields = metadata.get("fields")
        fields = []
        available_fields: set[str] = set()
        if isinstance(raw_fields, list):
            fields = [
                {
                    "name": field.get("name"),
                    "alias": field.get("alias"),
                    "type": field.get("type"),
                }
                for field in raw_fields
                if isinstance(field, dict)
            ]
            available_fields = {
                str(field["name"])
                for field in fields
                if isinstance(field.get("name"), str) and field.get("name")
            }

        requested_fields = distinct_fields or _DEFAULT_DISTINCT_FIELDS
        safe_distinct_fields = tuple(field for field in requested_fields if field in available_fields)
        distinct_values, distinct_value_errors = _query_distinct_values(
            layer_url,
            safe_distinct_fields,
            timeout,
        )
        if distinct_fields:
            for missing_field in sorted(set(distinct_fields) - available_fields):
                distinct_value_errors[missing_field] = "Field not present in layer metadata"

        query_formats = metadata.get("supportedQueryFormats")
        supported_query_formats = []
        if isinstance(query_formats, str):
            supported_query_formats = [
                value.strip() for value in query_formats.split(",") if value.strip()
            ]

        return ArcGISLayerProfile(
            source_id=source_id,
            url=layer_url,
            name=metadata.get("name"),
            layer_type=metadata.get("type"),
            geometry_type=metadata.get("geometryType"),
            feature_count=feature_count if isinstance(feature_count, int) else None,
            max_record_count=(
                metadata.get("maxRecordCount")
                if isinstance(metadata.get("maxRecordCount"), int)
                else None
            ),
            spatial_reference=_spatial_reference(metadata),
            extent=metadata.get("extent") if isinstance(metadata.get("extent"), dict) else None,
            wgs84_extent=wgs84_extent,
            fields=fields,
            distinct_values=distinct_values,
            distinct_value_errors=distinct_value_errors,
            supported_query_formats=supported_query_formats,
            capabilities=metadata.get("capabilities"),
        )
    except Exception as exc:
        return ArcGISLayerProfile(
            source_id=source_id,
            url=layer_url,
            name=None,
            layer_type=None,
            geometry_type=None,
            feature_count=None,
            max_record_count=None,
            spatial_reference=None,
            extent=None,
            wgs84_extent=None,
            fields=[],
            distinct_values={},
            distinct_value_errors={},
            supported_query_formats=[],
            capabilities=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def profile_catalog(path: str | Path, *, timeout: int = 30) -> dict[str, Any]:
    """Probe catalog entries that explicitly opt into ArcGIS source profiling."""
    _, records = load_source_catalog(path)
    profiles: list[dict[str, Any]] = []
    for record in records:
        probe = record.payload.get("probe")
        if not isinstance(probe, dict) or probe.get("type") != "arcgis-layer":
            continue
        url = probe.get("url")
        raw_distinct_fields = probe.get("distinct_fields", [])
        distinct_fields = (
            tuple(value for value in raw_distinct_fields if isinstance(value, str) and value)
            if isinstance(raw_distinct_fields, list)
            else ()
        )
        if not isinstance(url, str) or not url.startswith("https://"):
            profiles.append(
                asdict(
                    ArcGISLayerProfile(
                        source_id=record.source_id,
                        url=str(url or ""),
                        name=None,
                        layer_type=None,
                        geometry_type=None,
                        feature_count=None,
                        max_record_count=None,
                        spatial_reference=None,
                        extent=None,
                        wgs84_extent=None,
                        fields=[],
                        distinct_values={},
                        distinct_value_errors={},
                        supported_query_formats=[],
                        capabilities=None,
                        error="Invalid or non-HTTPS ArcGIS layer URL",
                    )
                )
            )
            continue
        profiles.append(
            asdict(
                profile_arcgis_layer(
                    record.source_id,
                    url,
                    distinct_fields=distinct_fields,
                    timeout=timeout,
                )
            )
        )
    return {"profiles": profiles}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe ArcGIS layers registered in the source qualification catalog."
    )
    parser.add_argument(
        "catalog",
        nargs="?",
        default="data/sources/qualification.json",
        help="Path to the qualification catalog.",
    )
    parser.add_argument("--output", required=True, help="JSON output path.")
    parser.add_argument("--timeout", type=int, default=30)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    report = profile_catalog(args.catalog, timeout=args.timeout)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
