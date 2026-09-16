from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ArcGISSnapshotReport:
    source_url: str
    retrieved_at_utc: str
    where: str
    requested_object_ids: int
    feature_count: int
    object_id_field: str | None
    server_max_record_count: int | None
    batch_size: int
    output: str
    sha256: str


def _request_json(
    url: str,
    timeout: int,
    *,
    form: dict[str, str] | None = None,
) -> dict[str, Any]:
    body = urlencode(form).encode("utf-8") if form is not None else None
    headers = {"User-Agent": "Raster-Analytics-Web/arcgis-ingestion"}
    if body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(url, data=body, headers=headers)
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ArcGIS response must be a JSON object")
    if "error" in payload:
        raise ValueError(f"ArcGIS error: {payload['error']}")
    return payload


def _metadata_url(layer_url: str) -> str:
    return f"{layer_url.rstrip('/')}?{urlencode({'f': 'json'})}"


def _ids_url(layer_url: str, where: str) -> str:
    params = {"where": where, "returnIdsOnly": "true", "f": "json"}
    return f"{layer_url.rstrip('/')}/query?{urlencode(params)}"


def _features_endpoint(layer_url: str) -> str:
    return f"{layer_url.rstrip('/')}/query"


def _features_form(
    object_ids: list[int],
    *,
    out_fields: str,
    out_sr: int,
) -> dict[str, str]:
    return {
        "objectIds": ",".join(str(value) for value in object_ids),
        "outFields": out_fields,
        "returnGeometry": "true",
        "outSR": str(out_sr),
        "f": "geojson",
    }


def _object_id_field(metadata: dict[str, Any]) -> str | None:
    field = metadata.get("objectIdField")
    if isinstance(field, str) and field:
        return field
    fields = metadata.get("fields")
    if isinstance(fields, list):
        for item in fields:
            if isinstance(item, dict) and item.get("type") == "esriFieldTypeOID":
                name = item.get("name")
                if isinstance(name, str) and name:
                    return name
    return None


def _effective_batch_size(
    metadata: dict[str, Any],
    requested: int | None,
) -> tuple[int, int | None]:
    if requested is not None and requested < 1:
        raise ValueError("batch_size must be positive")
    raw_limit = metadata.get("maxRecordCount")
    server_limit = raw_limit if isinstance(raw_limit, int) and raw_limit > 0 else None
    safe_server_limit = server_limit or 1000
    desired = requested or safe_server_limit
    return min(desired, safe_server_limit, 2000), server_limit


def fetch_arcgis_geojson(
    layer_url: str,
    output_path: str | Path,
    *,
    where: str = "1=1",
    out_fields: str = "*",
    out_sr: int = 4326,
    batch_size: int | None = None,
    timeout: int = 45,
) -> ArcGISSnapshotReport:
    """Create a complete local GeoJSON snapshot from a queryable ArcGIS layer.

    Object IDs are requested first and then fetched in sorted POST batches. POST avoids request-URI
    limits on large object-ID lists. Every batch is checked against its requested ID count so a
    server-side record cap cannot silently create a partial source snapshot.
    """
    if not layer_url.startswith("https://"):
        raise ValueError("ArcGIS source URL must use HTTPS")

    metadata = _request_json(_metadata_url(layer_url), timeout)
    ids_payload = _request_json(_ids_url(layer_url, where), timeout)
    raw_ids = ids_payload.get("objectIds")
    if raw_ids is None:
        raw_ids = []
    if not isinstance(raw_ids, list) or not all(isinstance(value, int) for value in raw_ids):
        raise ValueError("ArcGIS object-id query did not return an integer objectIds array")

    object_ids = sorted(set(raw_ids))
    effective_batch_size, server_limit = _effective_batch_size(metadata, batch_size)

    features: list[dict[str, Any]] = []
    for start in range(0, len(object_ids), effective_batch_size):
        batch = object_ids[start : start + effective_batch_size]
        payload = _request_json(
            _features_endpoint(layer_url),
            timeout,
            form=_features_form(
                batch,
                out_fields=out_fields,
                out_sr=out_sr,
            ),
        )
        batch_features = payload.get("features")
        if not isinstance(batch_features, list):
            raise ValueError("ArcGIS GeoJSON query did not return a features array")
        valid_features = [feature for feature in batch_features if isinstance(feature, dict)]
        if len(valid_features) != len(batch):
            raise ValueError(
                "ArcGIS batch was truncated or incomplete: "
                f"requested {len(batch)} IDs, received {len(valid_features)} features"
            )
        features.extend(valid_features)

    if len(features) != len(object_ids):
        raise ValueError(
            "ArcGIS snapshot feature count does not match the object-id inventory: "
            f"{len(features)} != {len(object_ids)}"
        )

    feature_collection = {
        "type": "FeatureCollection",
        "name": metadata.get("name") or "arcgis_snapshot",
        "crs": {"type": "name", "properties": {"name": f"EPSG:{out_sr}"}},
        "features": features,
    }
    rendered = json.dumps(
        feature_collection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered + "\n", encoding="utf-8")
    digest = hashlib.sha256((rendered + "\n").encode("utf-8")).hexdigest()

    return ArcGISSnapshotReport(
        source_url=layer_url,
        retrieved_at_utc=datetime.now(UTC).isoformat(),
        where=where,
        requested_object_ids=len(object_ids),
        feature_count=len(features),
        object_id_field=_object_id_field(metadata),
        server_max_record_count=server_limit,
        batch_size=effective_batch_size,
        output=str(destination),
        sha256=digest,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Snapshot an ArcGIS feature layer as GeoJSON.")
    parser.add_argument("layer_url")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report")
    parser.add_argument("--where", default="1=1")
    parser.add_argument("--out-fields", default="*")
    parser.add_argument("--out-sr", type=int, default=4326)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--timeout", type=int, default=45)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    report = fetch_arcgis_geojson(
        args.layer_url,
        args.output,
        where=args.where,
        out_fields=args.out_fields,
        out_sr=args.out_sr,
        batch_size=args.batch_size,
        timeout=args.timeout,
    )
    rendered = json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
