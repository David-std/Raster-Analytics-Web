from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_STATUSES = {"ACCEPTED", "CANDIDATE", "AUXILIARY", "BLOCKED", "REJECTED"}
_ALLOWED_EVIDENCE = {
    "PLANNED",
    "IMPLEMENTED_NOT_EXECUTED",
    "PROVEN_WITH_FIXTURE",
    "PROVEN_WITH_REAL_SOURCE",
    "BENCHMARKED",
    "VALIDATED_WITH_SPECIALIST",
    "BLOCKED",
    "REJECTED",
}
_REQUIRED_ROLE_GROUPS = {
    "outcome": {"outcome_event"},
    "severity": {"severity_outcome"},
    "pedestrian_exposure": {"pedestrian_exposure", "pedestrian_exposure_proxy"},
    "traffic_exposure": {"traffic_exposure", "traffic_exposure_proxy"},
    "built_environment": {"built_environment"},
    "geometry": {"analysis_geometry"},
    "temporal_context": {"temporal_context"},
}
_EXPOSURE_ROLES = {
    "pedestrian_exposure": ("pedestrian_exposure", "pedestrian_exposure_proxy"),
    "traffic_exposure": ("traffic_exposure", "traffic_exposure_proxy"),
}
_RESOLVED_STATES = {"READY", "READY_DIRECT", "READY_WITH_PROXY"}


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    publisher: str
    category: str
    status: str
    evidence_state: str
    model_roles: tuple[str, ...]
    payload: dict[str, Any]


def _required_string(source: dict[str, Any], key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Source {source.get('id', '<unknown>')} is missing non-empty '{key}'")
    return value.strip()


def _string_list(source: dict[str, Any], key: str) -> tuple[str, ...]:
    value = source.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Source {source.get('id', '<unknown>')} must define string list '{key}'")
    return tuple(item.strip() for item in value if item.strip())


def load_source_catalog(path: str | Path) -> tuple[dict[str, Any], list[SourceRecord]]:
    """Load and validate the curated source-qualification catalog."""
    catalog_path = Path(path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("Source catalog must contain a non-empty 'sources' array")

    records: list[SourceRecord] = []
    seen: set[str] = set()
    for source in raw_sources:
        if not isinstance(source, dict):
            raise ValueError("Every source catalog entry must be an object")
        source_id = _required_string(source, "id")
        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen.add(source_id)

        status = _required_string(source, "status")
        evidence_state = _required_string(source, "evidence_state")
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"Source {source_id} has invalid status {status!r}")
        if evidence_state not in _ALLOWED_EVIDENCE:
            raise ValueError(f"Source {source_id} has invalid evidence state {evidence_state!r}")

        access = source.get("access")
        coverage = source.get("coverage")
        grain = source.get("grain")
        if not isinstance(access, dict):
            raise ValueError(f"Source {source_id} must define an 'access' object")
        if not isinstance(coverage, dict):
            raise ValueError(f"Source {source_id} must define a 'coverage' object")
        if not isinstance(grain, dict):
            raise ValueError(f"Source {source_id} must define a 'grain' object")

        records.append(
            SourceRecord(
                source_id=source_id,
                publisher=_required_string(source, "publisher"),
                category=_required_string(source, "category"),
                status=status,
                evidence_state=evidence_state,
                model_roles=_string_list(source, "model_roles"),
                payload=source,
            )
        )
    return payload, records


def _summary_item(record: SourceRecord) -> dict[str, str]:
    return {
        "id": record.source_id,
        "status": record.status,
        "evidence_state": record.evidence_state,
    }


def _is_accepted_real(record: SourceRecord) -> bool:
    return record.status == "ACCEPTED" and record.evidence_state == "PROVEN_WITH_REAL_SOURCE"


def _is_partial_problem_scope(record: SourceRecord) -> bool:
    coverage = record.payload.get("coverage")
    return (
        isinstance(coverage, dict)
        and coverage.get("analytical_scope") == "partial_problem_scope"
    )


def _exposure_state(group: str, records: list[SourceRecord]) -> tuple[str, dict[str, Any]]:
    direct_role, proxy_role = _EXPOSURE_ROLES[group]
    direct = [record for record in records if direct_role in record.model_roles]
    proxies = [record for record in records if proxy_role in record.model_roles]
    accepted_direct = [record for record in direct if _is_accepted_real(record)]
    accepted_proxy = [record for record in proxies if _is_accepted_real(record)]

    if accepted_direct:
        state = "READY_DIRECT"
    elif accepted_proxy:
        state = "READY_WITH_PROXY"
    elif direct or proxies:
        state = "RESEARCH_REQUIRED"
    else:
        state = "BLOCKED"

    return state, {
        "direct_sources": [_summary_item(record) for record in direct],
        "proxy_sources": [_summary_item(record) for record in proxies],
    }


def build_readiness_summary(records: list[SourceRecord]) -> dict[str, Any]:
    """Summarize source fitness without turning source existence into model readiness."""
    role_sources: dict[str, dict[str, Any]] = {}
    for group, accepted_roles in _REQUIRED_ROLE_GROUPS.items():
        matching_records = [
            record for record in records if accepted_roles.intersection(record.model_roles)
        ]
        matches = [_summary_item(record) for record in matching_records]

        if group in _EXPOSURE_ROLES:
            state, exposure_detail = _exposure_state(group, matching_records)
            role_sources[group] = {
                "state": state,
                "sources": matches,
                **exposure_detail,
            }
            continue

        accepted = [record for record in matching_records if _is_accepted_real(record)]
        blocked = [record for record in matching_records if record.status == "BLOCKED"]
        partial_scope = [record for record in accepted if _is_partial_problem_scope(record)]
        if accepted and (blocked or partial_scope):
            # A blocked broader source or an accepted source explicitly marked as
            # narrower than the problem scope must not be mistaken for full coverage.
            state = "PARTIAL_SCOPE"
        elif accepted:
            state = "READY"
        elif matching_records:
            state = "RESEARCH_REQUIRED"
        else:
            state = "BLOCKED"
        role_sources[group] = {"state": state, "sources": matches}

    unresolved = [
        group
        for group, result in role_sources.items()
        if result["state"] not in _RESOLVED_STATES
    ]
    return {
        "source_count": len(records),
        "status_counts": dict(sorted(Counter(record.status for record in records).items())),
        "evidence_counts": dict(
            sorted(Counter(record.evidence_state for record in records).items())
        ),
        "role_readiness": role_sources,
        "model_ready": not unresolved,
        "unresolved_role_groups": unresolved,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the data-source qualification catalog and report readiness."
    )
    parser.add_argument(
        "catalog",
        nargs="?",
        default="data/sources/qualification.json",
        help="Path to the qualification catalog.",
    )
    parser.add_argument("--output", help="Optional JSON output path.")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    _, records = load_source_catalog(args.catalog)
    summary = build_readiness_summary(records)
    rendered = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
