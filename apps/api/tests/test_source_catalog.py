import json

import pytest

from pipelines.profiling.source_catalog import build_readiness_summary, load_source_catalog


def _catalog(tmp_path, sources):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"sources": sources}), encoding="utf-8")
    return path


def _source(source_id, status, evidence_state, roles):
    return {
        "id": source_id,
        "publisher": "Publisher",
        "category": "category",
        "status": status,
        "evidence_state": evidence_state,
        "model_roles": roles,
        "access": {"type": "test"},
        "coverage": {"geography": "test"},
        "grain": {"spatial": "test", "temporal": "test"},
    }


def test_source_catalog_reports_unresolved_exposure_roles(tmp_path) -> None:
    path = _catalog(
        tmp_path,
        [
            _source(
                "outcome",
                "ACCEPTED",
                "PROVEN_WITH_REAL_SOURCE",
                ["outcome_event"],
            ),
            _source(
                "built",
                "CANDIDATE",
                "PLANNED",
                ["built_environment"],
            ),
        ],
    )

    _, records = load_source_catalog(path)
    summary = build_readiness_summary(records)

    assert summary["role_readiness"]["outcome"]["state"] == "READY"
    assert summary["role_readiness"]["built_environment"]["state"] == "RESEARCH_REQUIRED"
    assert summary["role_readiness"]["pedestrian_exposure"]["state"] == "BLOCKED"
    assert summary["model_ready"] is False


def test_source_catalog_rejects_duplicate_ids(tmp_path) -> None:
    source = _source("duplicate", "CANDIDATE", "PLANNED", ["built_environment"])
    path = _catalog(tmp_path, [source, source])

    with pytest.raises(ValueError, match="Duplicate source id"):
        load_source_catalog(path)
