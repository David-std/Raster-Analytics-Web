import json
from io import BytesIO
from urllib.parse import parse_qs

import pytest

from pipelines.ingestion import arcgis


class _Response:
    def __init__(self, payload):
        self._stream = BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._stream.read()


def _form(request) -> dict[str, list[str]]:
    if request.data is None:
        return {}
    return parse_qs(request.data.decode("utf-8"))


def test_arcgis_snapshot_fetches_sorted_id_batches(monkeypatch, tmp_path) -> None:
    seen_forms = []

    def fake_urlopen(request, timeout):
        assert timeout == 10
        url = request.full_url
        form = _form(request)
        if form:
            seen_forms.append(form)
        if "returnIdsOnly=true" in url:
            return _Response({"objectIds": [3, 1, 2]})
        if not form:
            return _Response(
                {
                    "name": "Districts",
                    "maxRecordCount": 2,
                    "objectIdField": "OBJECTID",
                }
            )
        if form["objectIds"] == ["1,2"]:
            return _Response(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {"type": "Feature", "properties": {"OBJECTID": 1}, "geometry": None},
                        {"type": "Feature", "properties": {"OBJECTID": 2}, "geometry": None},
                    ],
                }
            )
        if form["objectIds"] == ["3"]:
            return _Response(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {"type": "Feature", "properties": {"OBJECTID": 3}, "geometry": None}
                    ],
                }
            )
        raise AssertionError(form)

    monkeypatch.setattr(arcgis, "urlopen", fake_urlopen)
    output = tmp_path / "snapshot.geojson"
    report = arcgis.fetch_arcgis_geojson(
        "https://example.test/MapServer/0",
        output,
        batch_size=9,
        timeout=10,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert report.requested_object_ids == 3
    assert report.feature_count == 3
    assert report.object_id_field == "OBJECTID"
    assert report.server_max_record_count == 2
    assert report.batch_size == 2
    assert len(report.sha256) == 64
    assert [item["properties"]["OBJECTID"] for item in payload["features"]] == [1, 2, 3]
    assert [form["objectIds"][0] for form in seen_forms] == ["1,2", "3"]


def test_arcgis_snapshot_rejects_server_side_truncation(monkeypatch, tmp_path) -> None:
    def fake_urlopen(request, timeout):
        assert timeout == 10
        url = request.full_url
        form = _form(request)
        if "returnIdsOnly=true" in url:
            return _Response({"objectIds": [1, 2]})
        if not form:
            return _Response({"name": "Layer", "maxRecordCount": 2})
        return _Response(
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {"OBJECTID": 1}, "geometry": None}
                ],
            }
        )

    monkeypatch.setattr(arcgis, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="truncated or incomplete"):
        arcgis.fetch_arcgis_geojson(
            "https://example.test/MapServer/0",
            tmp_path / "snapshot.geojson",
            timeout=10,
        )
