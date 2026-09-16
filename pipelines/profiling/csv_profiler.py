from __future__ import annotations

import csv
import hashlib
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pipelines.profiling.models import ColumnProfile, CoordinateProfile, DatasetProfile

_NULL_TOKENS = {"", "na", "n/a", "null", "none", "nan"}
_BOOLEAN_TOKENS = {"true", "false", "yes", "no", "si", "sí"}
_LATITUDE_NAMES = {"lat", "latitude", "latitud"}
_LONGITUDE_NAMES = {"lon", "lng", "long", "longitude", "longitud"}
_UNIQUE_TRACKING_LIMIT = 100_000
_SAMPLE_VALUE_LIMIT = 5
_TYPE_CONFIDENCE_THRESHOLD = 0.90


def _normalise_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def _is_null(value: str | None) -> bool:
    return value is None or value.strip().casefold() in _NULL_TOKENS


def _parse_datetime(value: str) -> datetime | None:
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        pass

    formats = (
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    )
    for date_format in formats:
        try:
            return datetime.strptime(candidate, date_format)
        except ValueError:
            continue
    return None


def _format_number(value: float | None) -> str | None:
    if value is None:
        return None
    if value.is_integer():
        return str(int(value))
    return format(value, ".12g")


class _ColumnAccumulator:
    def __init__(self, name: str) -> None:
        self.name = name
        self.null_count = 0
        self.non_null_count = 0
        self.type_counts: Counter[str] = Counter()
        self.unique_hashes: set[bytes] = set()
        self.unique_count_is_capped = False
        self.sample_values: list[str] = []
        self.numeric_min: float | None = None
        self.numeric_max: float | None = None
        self.datetime_min: datetime | None = None
        self.datetime_max: datetime | None = None

    def add(self, raw_value: str | None) -> None:
        if _is_null(raw_value):
            self.null_count += 1
            return

        assert raw_value is not None
        value = raw_value.strip()
        self.non_null_count += 1
        self._track_unique(value)
        self._track_sample(value)
        self._classify(value)

    def _track_unique(self, value: str) -> None:
        if len(self.unique_hashes) >= _UNIQUE_TRACKING_LIMIT:
            self.unique_count_is_capped = True
            return
        digest = hashlib.blake2b(value.encode("utf-8"), digest_size=16).digest()
        self.unique_hashes.add(digest)

    def _track_sample(self, value: str) -> None:
        if len(self.sample_values) >= _SAMPLE_VALUE_LIMIT or value in self.sample_values:
            return
        self.sample_values.append(value)

    def _classify(self, value: str) -> None:
        normalised = value.casefold()
        if normalised in _BOOLEAN_TOKENS:
            self.type_counts["boolean"] += 1
            return

        try:
            integer_value = int(value)
        except ValueError:
            integer_value = None
        if integer_value is not None:
            self.type_counts["integer"] += 1
            self._track_numeric(float(integer_value))
            return

        try:
            float_value = float(value)
        except ValueError:
            float_value = None
        if float_value is not None:
            self.type_counts["float"] += 1
            self._track_numeric(float_value)
            return

        datetime_value = _parse_datetime(value)
        if datetime_value is not None:
            self.type_counts["datetime"] += 1
            self._track_datetime(datetime_value)
            return

        self.type_counts["string"] += 1

    def _track_numeric(self, value: float) -> None:
        self.numeric_min = value if self.numeric_min is None else min(self.numeric_min, value)
        self.numeric_max = value if self.numeric_max is None else max(self.numeric_max, value)

    def _track_datetime(self, value: datetime) -> None:
        comparable = value.replace(tzinfo=None) if value.tzinfo is not None else value
        self.datetime_min = (
            comparable if self.datetime_min is None else min(self.datetime_min, comparable)
        )
        self.datetime_max = (
            comparable if self.datetime_max is None else max(self.datetime_max, comparable)
        )

    def profile(self, row_count: int) -> ColumnProfile:
        inferred_type, parse_success_pct = self._infer_type()
        minimum: str | None = None
        maximum: str | None = None
        if inferred_type in {"integer", "float"}:
            minimum = _format_number(self.numeric_min)
            maximum = _format_number(self.numeric_max)
        elif inferred_type == "datetime":
            minimum = self.datetime_min.isoformat() if self.datetime_min else None
            maximum = self.datetime_max.isoformat() if self.datetime_max else None

        null_pct = round((self.null_count / row_count * 100) if row_count else 0.0, 2)
        return ColumnProfile(
            name=self.name,
            inferred_type=inferred_type,
            non_null_count=self.non_null_count,
            null_count=self.null_count,
            null_pct=null_pct,
            unique_count=len(self.unique_hashes),
            unique_count_is_capped=self.unique_count_is_capped,
            parse_success_pct=parse_success_pct,
            minimum=minimum,
            maximum=maximum,
            sample_values=list(self.sample_values),
        )

    def _infer_type(self) -> tuple[str, float | None]:
        if self.non_null_count == 0:
            return "empty", None

        total = self.non_null_count
        numeric_count = self.type_counts["integer"] + self.type_counts["float"]
        candidates = {
            "boolean": self.type_counts["boolean"],
            "numeric": numeric_count,
            "datetime": self.type_counts["datetime"],
        }
        inferred_family, parsed_count = max(candidates.items(), key=lambda item: item[1])
        ratio = parsed_count / total
        if ratio < _TYPE_CONFIDENCE_THRESHOLD:
            return "string", None

        parse_success_pct = round(ratio * 100, 2)
        if inferred_family == "numeric":
            numeric_type = "float" if self.type_counts["float"] else "integer"
            return numeric_type, parse_success_pct
        return inferred_family, parse_success_pct


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _detect_delimiter(path: Path, encoding: str) -> str:
    with path.open("r", encoding=encoding, newline="") as source:
        sample = source.read(8192)
    if not sample:
        return ","
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def _coordinate_columns(fieldnames: list[str]) -> tuple[str | None, str | None]:
    latitude_column: str | None = None
    longitude_column: str | None = None
    for fieldname in fieldnames:
        normalised = _normalise_name(fieldname)
        if latitude_column is None and normalised in _LATITUDE_NAMES:
            latitude_column = fieldname
        if longitude_column is None and normalised in _LONGITUDE_NAMES:
            longitude_column = fieldname
    return latitude_column, longitude_column


def profile_csv(
    path: str | Path,
    *,
    delimiter: str | None = None,
    encoding: str = "utf-8-sig",
) -> DatasetProfile:
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)

    chosen_delimiter = delimiter or _detect_delimiter(csv_path, encoding)
    row_count = 0
    duplicate_row_count = 0
    malformed_row_count = 0
    seen_rows: set[bytes] = set()
    paired_coordinate_count = 0
    valid_coordinate_count = 0

    with csv_path.open("r", encoding=encoding, newline="") as source:
        reader = csv.DictReader(source, delimiter=chosen_delimiter)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("CSV has no header row")
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("CSV contains duplicate header names")

        accumulators = {name: _ColumnAccumulator(name) for name in fieldnames}
        latitude_column, longitude_column = _coordinate_columns(fieldnames)

        for row in reader:
            row_count += 1
            if None in row:
                malformed_row_count += 1

            values = tuple((row.get(name) or "").strip() for name in fieldnames)
            row_digest = hashlib.blake2b(repr(values).encode("utf-8"), digest_size=16).digest()
            if row_digest in seen_rows:
                duplicate_row_count += 1
            else:
                seen_rows.add(row_digest)

            for name, accumulator in accumulators.items():
                accumulator.add(row.get(name))

            if latitude_column and longitude_column:
                raw_latitude = row.get(latitude_column)
                raw_longitude = row.get(longitude_column)
                if not _is_null(raw_latitude) and not _is_null(raw_longitude):
                    paired_coordinate_count += 1
                    try:
                        latitude = float(raw_latitude or "")
                        longitude = float(raw_longitude or "")
                    except ValueError:
                        continue
                    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                        valid_coordinate_count += 1

    column_profiles = [accumulators[name].profile(row_count) for name in fieldnames]
    coordinate_profile: CoordinateProfile | None = None
    if latitude_column and longitude_column:
        valid_pct = (
            valid_coordinate_count / paired_coordinate_count * 100
            if paired_coordinate_count
            else 0.0
        )
        coordinate_profile = CoordinateProfile(
            latitude_column=latitude_column,
            longitude_column=longitude_column,
            paired_non_null_count=paired_coordinate_count,
            valid_coordinate_count=valid_coordinate_count,
            valid_coordinate_pct=round(valid_pct, 2),
        )

    temporal_candidates = [
        profile.name for profile in column_profiles if profile.inferred_type == "datetime"
    ]
    warnings: list[str] = []
    if row_count == 0:
        warnings.append("Dataset contains no data rows.")
    if duplicate_row_count:
        warnings.append(f"Detected {duplicate_row_count} exact duplicate row(s).")
    if malformed_row_count:
        warnings.append(f"Detected {malformed_row_count} malformed row(s) with extra fields.")
    if coordinate_profile is None:
        warnings.append("No explicit latitude/longitude column pair was detected.")
    elif coordinate_profile.valid_coordinate_pct < 90:
        warnings.append("Less than 90% of non-null coordinate pairs are geographically valid.")
    if not temporal_candidates:
        warnings.append("No temporal column reached the 90% datetime parse threshold.")
    for profile in column_profiles:
        if profile.null_pct >= 50:
            warnings.append(f"Column '{profile.name}' is at least 50% null.")
        if profile.unique_count_is_capped:
            warnings.append(
                f"Column '{profile.name}' unique count reached the tracking cap "
                f"({_UNIQUE_TRACKING_LIMIT})."
            )

    duplicate_pct = round(
        (duplicate_row_count / row_count * 100) if row_count else 0.0,
        2,
    )
    return DatasetProfile(
        source=str(csv_path),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        file_size_bytes=csv_path.stat().st_size,
        sha256=_sha256(csv_path),
        delimiter=chosen_delimiter,
        row_count=row_count,
        column_count=len(fieldnames),
        duplicate_row_count=duplicate_row_count,
        duplicate_row_pct=duplicate_pct,
        columns=column_profiles,
        coordinate_profile=coordinate_profile,
        temporal_candidates=temporal_candidates,
        warnings=warnings,
    )
