import json
from io import BytesIO

from pipelines.profiling import arcgis_profiler


class _Response:
    def __init__(self, payload):
        self._stream = BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._stream.read()


def test_arcgis_layer_profile_uses_metadata_and_count(monkeypatch) -> None:
    metadata = {
        "name": "Cruces Peatonales",
        "type": "Feature Layer",
        "geometryType": "esriGeometryPoint",
        "maxRecordCount": 1000,
        "supportedQueryFormats": "JSON, geoJSON",
        "capabilities": "Map,Query,Data",
        "extent": {
            "xmin": 1,
            "ymin": 2,
            "xmax": 3,
            "ymax": 4,
            "spatialReference": {"wkid": 32718},
        },
        "fields": [
            {"name": "OBJECTID", "alias": "OBJECTID", "type": "esriFieldTypeOID"},
            {"name": "DISTRICT", "alias": "District", "type": "esriFieldTypeString"},
        ],
    }
    count = {"count": 321}

    def fake_urlopen(request, timeout):
        assert timeout == 10
        return _Response(count if "/query?" in request.full_url else metadata)

    monkeypatch.setattr(arcgis_profiler, "urlopen", fake_urlopen)

    profile = arcgis_profiler.profile_arcgis_layer(
        "crossings",
        "https://example.test/MapServer/1",
        timeout=10,
    )

    assert profile.error is None
    assert profile.name == "Cruces Peatonales"
    assert profile.geometry_type == "esriGeometryPoint"
    assert profile.feature_count == 321
    assert profile.spatial_reference == 32718
    assert profile.supported_query_formats == ["JSON", "geoJSON"]
    assert profile.fields[1]["name"] == "DISTRICT"


def test_arcgis_layer_profile_returns_explicit_error(monkeypatch) -> None:
    def failing_urlopen(_request, timeout):
        raise TimeoutError(f"timeout={timeout}")

    monkeypatch.setattr(arcgis_profiler, "urlopen", failing_urlopen)

    profile = arcgis_profiler.profile_arcgis_layer(
        "source",
        "https://example.test/MapServer/2",
        timeout=5,
    )

    assert profile.feature_count is None
    assert profile.error == "TimeoutError: timeout=5"
