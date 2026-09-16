from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

_DEFAULT_DISTRICTS = Path("data/reference/lima_metropolitana_districts.json")


def _key(value: Any) -> str:
    if value is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^A-Za-z0-9]+", " ", without_marks).upper().split())


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _parse_time(value: str) -> bool:
    if not value:
        return False
    for pattern in ("%H:%M", "%H:%M:%S"):
        try:
            datetime.strptime(value, pattern)
            return True
        except ValueError:
            continue
    return False


def load_expected_districts(path: str | Path = _DEFAULT_DISTRICTS) -> set[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    districts = payload.get("districts")
    if not isinstance(districts, list) or not districts:
        raise ValueError("District reference must contain a non-empty 'districts' array")
    normalized = {_key(value) for value in districts if isinstance(value, str) and value.strip()}
    if len(normalized) != len(districts):
        raise ValueError("District reference contains duplicates or invalid values")
    return normalized


def profile_onsv_pedestrian_events(
    csv_path: str | Path,
    *,
    district_reference: str | Path = _DEFAULT_DISTRICTS,
) -> dict[str, Any]:
    """Profile semantic and geographic suitability of normalized ONSV pedestrian events.

    A person classified as PEATON in a fatal crash is not automatically equivalent to a
    crash whose recorded class is ATROPELLO. The report exposes both populations so target
    selection remains an explicit analytical decision rather than an ingestion side effect.
    """
    expected_districts = load_expected_districts(district_reference)
    path = Path(csv_path)
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    by_year: Counter[str] = Counter()
    by_class: Counter[str] = Counter()
    by_district: Counter[str] = Counter()
    strict_atropello_by_year: Counter[str] = Counter()
    broader_pedestrian_linked_by_year: Counter[str] = Counter()
    year_dates: dict[str, list[date]] = defaultdict(list)
    valid_times = 0
    class_contains_atropello = 0
    class_not_atropello = 0
    fatalities_in_non_atropello = 0

    for row in rows:
        year = str(row.get("year") or "").strip()
        crash_class = _key(row.get("crash_class"))
        district = _key(row.get("district"))
        parsed_date = _parse_date(str(row.get("crash_date") or ""))

        if year:
            by_year[year] += 1
            broader_pedestrian_linked_by_year[year] += 1
            if parsed_date:
                year_dates[year].append(parsed_date)
        if crash_class:
            by_class[crash_class] += 1
        if district:
            by_district[district] += 1
        if _parse_time(str(row.get("crash_time") or "")):
            valid_times += 1

        if "ATROPELLO" in crash_class:
            class_contains_atropello += 1
            if year:
                strict_atropello_by_year[year] += 1
        else:
            class_not_atropello += 1
            try:
                fatalities_in_non_atropello += int(row.get("pedestrian_fatalities") or 0)
            except ValueError:
                pass

    observed_districts = set(by_district)
    unexpected_districts = sorted(observed_districts - expected_districts)
    missing_districts = sorted(expected_districts - observed_districts)

    year_coverage = {}
    for year, dates in sorted(year_dates.items()):
        year_coverage[year] = {
            "pedestrian_linked_fatal_crashes": by_year[year],
            "strict_atropello_class_crashes": strict_atropello_by_year[year],
            "other_pedestrian_linked_crashes": by_year[year] - strict_atropello_by_year[year],
            "first_date": min(dates).isoformat(),
            "last_date": max(dates).isoformat(),
        }

    return {
        "source": str(path),
        "rows": len(rows),
        "year_coverage": year_coverage,
        "crash_class_distribution": dict(by_class.most_common()),
        "target_population_candidates": {
            "strict_atropello_class": {
                "definition": "Recorded crash class contains ATROPELLO.",
                "rows": class_contains_atropello,
                "by_year": dict(sorted(strict_atropello_by_year.items())),
                "status": "CANDIDATE_NOT_SELECTED",
            },
            "broader_pedestrian_linked_fatal_crash": {
                "definition": "Fatal crash has at least one linked person classified as PEATON.",
                "rows": len(rows),
                "by_year": dict(sorted(broader_pedestrian_linked_by_year.items())),
                "status": "CANDIDATE_NOT_SELECTED",
            },
        },
        "class_name_contains_atropello": class_contains_atropello,
        "class_name_not_contains_atropello": class_not_atropello,
        "pedestrian_fatalities_in_non_atropello_class": fatalities_in_non_atropello,
        "time_parse_success_pct": round((valid_times / len(rows) * 100), 2) if rows else 0.0,
        "district_coverage": {
            "expected_count": len(expected_districts),
            "observed_count": len(observed_districts & expected_districts),
            "missing": missing_districts,
            "unexpected": unexpected_districts,
            "events_by_district": dict(by_district.most_common()),
        },
        "semantic_warning": (
            "Rows are selected because a PEATON person is linked to the fatal crash. "
            "The recorded crash class is heterogeneous; do not call every row an atropello "
            "until the target inclusion rule is explicitly defined and reviewed."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit geographic and crash-class suitability of normalized ONSV events."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--district-reference", type=Path, default=_DEFAULT_DISTRICTS)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    report = profile_onsv_pedestrian_events(
        args.source,
        district_reference=args.district_reference,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
