import json
from pathlib import Path

from ml import datasets as ds

CATALOG_PATH = Path("data/features/catalog.json")
SOURCE_CATALOG_PATH = Path("data/sources/qualification.json")
EXPOSURE_STRATEGY_PATH = Path("data/features/exposure-strategy.json")


def _source_records() -> dict[str, dict]:
    payload = json.loads(SOURCE_CATALOG_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["sources"]}


def _strategy() -> dict:
    return json.loads(EXPOSURE_STRATEGY_PATH.read_text(encoding="utf-8"))


def test_exposure_strategy_references_known_features_and_sources() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    sources = _source_records()
    strategy = _strategy()

    pedestrian = strategy["pedestrian_exposure"]
    vehicle = strategy["vehicle_exposure"]

    for feature_id in pedestrian["proxy_components"]:
        assert feature_id in catalog.features

    referenced_sources = set(pedestrian["direct_measure"]["candidate_sources"])
    referenced_sources.update(pedestrian["local_validation_signal"]["source_ids"])
    referenced_sources.update(vehicle["direct_measure"]["candidate_sources"])
    referenced_sources.update(vehicle["context_only_sources"])

    assert referenced_sources <= set(sources)


def test_proxy_components_cannot_be_used_as_exposure_offsets() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    strategy = _strategy()

    for feature_id in strategy["pedestrian_exposure"]["proxy_components"]:
        feature = catalog.features[feature_id]
        assert feature.can_be_exposure_offset is False


def test_direct_exposure_source_is_still_blocked() -> None:
    sources = _source_records()
    strategy = _strategy()

    direct_sources = strategy["pedestrian_exposure"]["direct_measure"]["candidate_sources"]
    assert direct_sources
    assert all(sources[source_id]["status"] == "BLOCKED" for source_id in direct_sources)


def test_local_transit_validation_is_not_declared_citywide_exposure() -> None:
    strategy = _strategy()
    local_signal = strategy["pedestrian_exposure"]["local_validation_signal"]

    assert local_signal["status"] == "CANDIDATE"
    assert "citywide_pedestrian_count" in local_signal["forbidden_uses"]
    assert "citywide_exposure_denominator" in local_signal["forbidden_uses"]


def test_fallback_semantics_forbid_exposure_normalized_probability_claim() -> None:
    strategy = _strategy()
    fallback = strategy["fallback_product_semantics"]

    assert "relative analytical risk/frequency" in fallback["if_direct_exposure_remains_unavailable"]
    assert "exposure-normalized" in fallback["forbidden_claim"]


def test_exposure_gate_requires_ablation() -> None:
    strategy = _strategy()
    exit_conditions = strategy["exit_conditions"]

    assert any("ablation" in condition.lower() for condition in exit_conditions)
    assert any("lagged outcome history" in condition.lower() for condition in exit_conditions)
