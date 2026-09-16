from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pipelines.profiling.source_catalog import load_source_catalog


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
    fields: list[dict[str, Any]]
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


def _spatial_reference(metadata: dict[str, Any]) -> int | str | None:
    extent = metadata.get("extent")
    if not isinstance(extent, dict):
        return None
    spatial_reference = extent.get("spatialReference")
    if not isinstance(spatial_reference, dict):
        return None
    return spatial_reference.get("latestWkid") or spatial_reference.get("wkid")


def profile_arcgis_layer(source_id: str, layer_url: str, *, timeout: int = 30) -> ArcGISLayerProfile:
    """Profile an ArcGIS feature layer from metadata and count endpoints only."""
    try:
        metadata = _json_request(_metadata_url(layer_url), timeout)
        count_payload = _json_request(_count_url(layer_url), timeout)
        feature_count = count_payload.get("count")
        raw_fields = metadata.get("fields")
        fields = []
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
            fields=fields,
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
            fields=[],
            supported_query_formats=[],
            capabilities=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def profile_catalog(path: str | Path, *, timeout: int = 30) -> dict[str, Any]:
    """Probe catalog entries that explicitly opt into ArcGIS metadata profiling."""
    _, records = load_source_catalog(path)
    profiles: list[dict[str, Any]] = []
    for record in records:
        probe = record.payload.get("probe")
        if not isinstance(probe, dict) or probe.get("type") != "arcgis-layer":
            continue
        url = probe.get("url")
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
                        fields=[],
                        supported_query_formats=[],
                        capabilities=None,
                        error="Invalid or non-HTTPS ArcGIS layer URL",
                    )
                )
            )
            continue
        profiles.append(asdict(profile_arcgis_layer(record.source_id, url, timeout=timeout)))
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
