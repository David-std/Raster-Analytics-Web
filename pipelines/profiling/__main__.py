import argparse
import json
from pathlib import Path

from pipelines.profiling.csv_profiler import profile_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profile a CSV dataset without making project-model assumptions."
    )
    parser.add_argument("source", type=Path, help="CSV file to profile")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument("--delimiter", help="Optional delimiter override")
    parser.add_argument("--encoding", default="utf-8-sig", help="Input encoding")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = profile_csv(
        args.source,
        delimiter=args.delimiter,
        encoding=args.encoding,
    )
    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Profile written to {args.output}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
