import json
from io import BytesIO

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


def test_arcgis_snapshot_fetches_sorted_id_batches(monkeypatch, tmp_path) -> None:
    seen_urls = []

    def fake_urlopen(request, timeout):
        assert timeout == 10
        url = request.full_url
        seen_urls.append(url)
        if "returnIdsOnly=true" in url:
            return _Response({"objectIds": [3, 1, 2]})
        if "/query?" not in url:
            return _Response(
                {
                    "name": "Districts",
                    "maxRecordCount": 2,
                    "objectIdField": "OBJECTID",
                }
            )
        if "objectIds=1%2C2" in url:
            return _Response(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {"type": "Feature", "properties": {"OBJECTID": 1}, "geometry": None},
                        {"type": "Feature", "properties": {"OBJECTID": 2}, "geometry": None},
                    ],
                }
            )
        if "objectIds=3" in url:
            return _Response(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {"type": "Feature", "properties": {"OBJECTID": 3}, "geometry": None}
                    ],
                }
            )
        raise AssertionError(url)

    monkeypatch.setattr(arcgis, "urlopen", fake_urlopen)
    output = tmp_path / "snapshot.geojson"
    report = arcgis.fetch_arcgis_geojson(
        "https://example.test/MapServer/0",
        output,
        batch_size=2,
        timeout=10,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert report.requested_object_ids == 3
    assert report.feature_count == 3
    assert report.object_id_field == "OBJECTID"
    assert len(report.sha256) == 64
    assert [item["properties"]["OBJECTID"] for item in payload["features"]] == [1, 2, 3]
    assert sum("objectIds=" in url for url in seen_urls) == 2
