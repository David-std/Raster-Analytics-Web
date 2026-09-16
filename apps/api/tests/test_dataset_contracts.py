import json
from pathlib import Path

import pytest
from ml import datasets as ds


CATALOG_PATH = Path("data/features/catalog.json")
SOURCE_CATALOG_PATH = Path("data/sources/qualification.json")


def test_repository_contract_catalog_is_valid() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)

    assert catalog.version == 1
    assert catalog.features["direct_pedestrian_exposure"].status is ds.ContractStatus.BLOCKED
    assert catalog.targets["fatal_pedestrian_exposure_rate"].status is ds.ContractStatus.BLOCKED
    assert catalog.targets["pedestrian_linked_fatal_count"].status is ds.ContractStatus.CANDIDATE


def test_feature_lineage_references_qualified_source_ids() -> None:
    feature_catalog = ds.load_contract_catalog(CATALOG_PATH)
    source_catalog = json.loads(SOURCE_CATALOG_PATH.read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in source_catalog["sources"]}

    missing = {
        source_id
        for feature in feature_catalog.feature_definitions
        for source_id in feature.source_ids
        if source_id not in source_ids
    }
    assert missing == set()


def test_proxy_exposure_cannot_be_promoted_to_offset() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)

    with pytest.raises(ValueError, match="only qualified direct exposure"):
        catalog.require_exposure_offset("population_density_static")


def test_blocked_direct_exposure_cannot_be_used_as_offset_yet() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)

    with pytest.raises(ValueError, match="not available"):
        catalog.require_exposure_offset("direct_pedestrian_exposure")


def test_active_exposure_normalized_target_cannot_depend_on_blocked_feature() -> None:
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    target = next(item for item in raw["targets"] if item["id"] == "fatal_pedestrian_exposure_rate")
    target["status"] = "CANDIDATE"

    with pytest.raises(ValueError, match="active target depends on unavailable features"):
        ds.ContractCatalog.from_dict(raw)


def test_outcome_history_contract_must_be_lagged() -> None:
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    feature = next(
        item
        for item in raw["features"]
        if item["id"] == "lagged_pedestrian_linked_fatal_count_1m"
    )
    feature["temporal_semantics"] = "same_period"
    feature.pop("minimum_lag_periods", None)

    with pytest.raises(ValueError, match="outcome history must be lagged"):
        ds.ContractCatalog.from_dict(raw)


def test_temporal_split_is_ordered_and_2025_is_not_benchmark_data() -> None:
    split = ds.TemporalSplit.current_fatal_outcome_split()

    assert split.partition_for("2021-01") == "train"
    assert split.partition_for("2023-06") == "validation"
    assert split.partition_for("2024-12") == "test"
    assert split.partition_for("2025-01") is None

    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        ds.TemporalSplit(
            train=ds.DateWindow("train", "2021-01", "2023-03"),
            validation=ds.DateWindow("validation", "2023-01", "2023-12"),
            test=ds.DateWindow("test", "2024-01", "2024-12"),
        )


def test_builder_preserves_missingness_instead_of_imputing_zero() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    builder = ds.LeakageSafeDatasetBuilder(catalog, ds.TemporalSplit.current_fatal_outcome_split())

    rows = builder.build(
        target_id="pedestrian_linked_fatal_count",
        feature_ids=["month_of_year_sin", "transit_stop_density"],
        targets=[ds.TargetObservation("pedestrian_linked_fatal_count", "cell-1", "2024-01", 1)],
        features=[
            ds.FeatureObservation(
                feature_id="month_of_year_sin",
                spatial_unit_id="cell-1",
                target_period_id="2024-01",
                state=ds.ObservationState.OBSERVED,
                value=0.5,
            ),
            ds.FeatureObservation(
                feature_id="transit_stop_density",
                spatial_unit_id="cell-1",
                target_period_id="2024-01",
                state=ds.ObservationState.OUTSIDE_SOURCE_COVERAGE,
                value=None,
            ),
        ],
    )

    assert len(rows) == 1
    assert rows[0].partition == "test"
    assert rows[0].feature_values["transit_stop_density"] is None
    assert (
        rows[0].feature_states["transit_stop_density"]
        is ds.ObservationState.OUTSIDE_SOURCE_COVERAGE
    )


def test_builder_inserts_missing_state_when_feature_observation_is_absent() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    builder = ds.LeakageSafeDatasetBuilder(catalog, ds.TemporalSplit.current_fatal_outcome_split())

    row = builder.build(
        target_id="pedestrian_linked_fatal_count",
        feature_ids=["month_of_year_cos"],
        targets=[ds.TargetObservation("pedestrian_linked_fatal_count", "cell-1", "2022-04", 0)],
        features=[],
    )[0]

    assert row.feature_values["month_of_year_cos"] is None
    assert row.feature_states["month_of_year_cos"] is ds.ObservationState.MISSING


def test_builder_rejects_same_period_outcome_history_leakage() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    builder = ds.LeakageSafeDatasetBuilder(catalog, ds.TemporalSplit.current_fatal_outcome_split())

    with pytest.raises(ValueError, match="requires at least 1 period lag"):
        builder.build(
            target_id="pedestrian_linked_fatal_count",
            feature_ids=["lagged_pedestrian_linked_fatal_count_1m"],
            targets=[ds.TargetObservation("pedestrian_linked_fatal_count", "cell-1", "2024-01", 1)],
            features=[
                ds.FeatureObservation(
                    feature_id="lagged_pedestrian_linked_fatal_count_1m",
                    spatial_unit_id="cell-1",
                    target_period_id="2024-01",
                    observation_period_id="2024-01",
                    state=ds.ObservationState.OBSERVED,
                    value=1,
                )
            ],
        )


def test_builder_accepts_properly_lagged_outcome_history() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    builder = ds.LeakageSafeDatasetBuilder(catalog, ds.TemporalSplit.current_fatal_outcome_split())

    rows = builder.build(
        target_id="pedestrian_linked_fatal_count",
        feature_ids=["lagged_pedestrian_linked_fatal_count_12m"],
        targets=[ds.TargetObservation("pedestrian_linked_fatal_count", "cell-1", "2024-01", 1)],
        features=[
            ds.FeatureObservation(
                feature_id="lagged_pedestrian_linked_fatal_count_12m",
                spatial_unit_id="cell-1",
                target_period_id="2024-01",
                observation_period_id="2023-01",
                state=ds.ObservationState.OBSERVED,
                value=2,
            )
        ],
    )

    assert rows[0].feature_values["lagged_pedestrian_linked_fatal_count_12m"] == 2


def test_non_observed_missingness_states_cannot_carry_fabricated_values() -> None:
    catalog = ds.load_contract_catalog(CATALOG_PATH)
    builder = ds.LeakageSafeDatasetBuilder(catalog, ds.TemporalSplit.current_fatal_outcome_split())

    with pytest.raises(ValueError, match="must not fabricate a value"):
        builder.build(
            target_id="pedestrian_linked_fatal_count",
            feature_ids=["transit_stop_density"],
            targets=[ds.TargetObservation("pedestrian_linked_fatal_count", "cell-1", "2024-01", 0)],
            features=[
                ds.FeatureObservation(
                    feature_id="transit_stop_density",
                    spatial_unit_id="cell-1",
                    target_period_id="2024-01",
                    state=ds.ObservationState.OUTSIDE_SOURCE_COVERAGE,
                    value=0,
                )
            ],
        )
