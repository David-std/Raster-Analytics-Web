from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    inferred_type: str
    non_null_count: int
    null_count: int
    null_pct: float
    unique_count: int
    unique_count_is_capped: bool
    parse_success_pct: float | None
    minimum: str | None
    maximum: str | None
    sample_values: list[str]


@dataclass(frozen=True)
class CoordinateProfile:
    latitude_column: str
    longitude_column: str
    paired_non_null_count: int
    valid_coordinate_count: int
    valid_coordinate_pct: float


@dataclass(frozen=True)
class DatasetProfile:
    source: str
    generated_at_utc: str
    file_size_bytes: int
    sha256: str
    delimiter: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    duplicate_row_pct: float
    columns: list[ColumnProfile]
    coordinate_profile: CoordinateProfile | None
    temporal_candidates: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
