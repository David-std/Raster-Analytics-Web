import json

from pipelines.representation.support import load_support_mask


def test_support_mask_normalizes_arcgis_null_measure_ordinates(tmp_path) -> None:
    support = tmp_path / "support.geojson"
    support.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"distrito": "ALFA", "Anio": 2021},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-77.10, -12.10, 0, None],
                                    [-77.05, -12.10, 0, None],
                                    [-77.05, -12.00, 0, None],
                                    [-77.10, -12.00, 0, None],
                                    [-77.10, -12.10, 0, None],
                                ]
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    mask = load_support_mask(
        support,
        expected_districts={"ALFA"},
        district_field="distrito",
        support_label="test_support",
        source_crs="EPSG:4326",
    )

    assert mask.profile.retained_feature_count == 1
    assert mask.profile.invalid_geometry_count == 0
    assert mask.profile.normalized_extra_ordinate_count == 1
    assert mask.profile.retained_districts == ["ALFA"]
