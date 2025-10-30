from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

from .output import render_csv, render_html, render_json
from .scanner import scan_directory


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Traverse a directory tree and summarise folders that contain an "
            "important number of files."
        )
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Root directory (UNC paths such as \\server\\share are supported)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth to traverse below the root (default: 3)",
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=3,
        help="Minimum number of files required for a folder to be included (default: 3)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "csv", "both", "all"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output file path. For --format both this should be a directory "
            "where json and html files will be written."
        ),
    )
    parser.add_argument(
        "--comments-file",
        type=Path,
        help=(
            "Optional JSON file that maps folder paths to comments to pre-populate "
            "the output."
        ),
    )
    return parser.parse_args(argv)


def load_comments(path: Path | None) -> Dict[str, str]:
    if path is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"Comments file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse comments file {path}: {exc}") from None

    if not isinstance(data, dict):
        raise SystemExit("Comments file must be a JSON object mapping paths to strings")

    normalised: Dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise SystemExit("Every comment must be a string")
        normalised[str(key)] = value
    return normalised


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.root.exists() or not args.root.is_dir():
        raise SystemExit(f"Root path is not a directory: {args.root}")

    root_path = args.root.resolve()

    comments = load_comments(args.comments_file)
    result = scan_directory(
        root_path,
        max_depth=args.max_depth,
        min_files=args.min_files,
        comments=comments,
    )

    json_output = render_json(result, root_path, args.max_depth, args.min_files)
    html_output = render_html(result, root_path, args.max_depth, args.min_files)
    csv_output = render_csv(result, root_path, args.max_depth, args.min_files)

    if args.format == "json":
        if args.output:
            args.output.write_text(json_output, encoding="utf-8")
        else:
            sys.stdout.write(json_output)
            sys.stdout.write("\n")
        return 0

    if args.format == "html":
        if args.output:
            args.output.write_text(html_output, encoding="utf-8")
        else:
            sys.stdout.write(html_output)
        return 0

    if args.format == "csv":
        if args.output:
            args.output.write_text(csv_output, encoding="utf-8")
        else:
            sys.stdout.write(csv_output)
            if not csv_output.endswith("\n"):
                sys.stdout.write("\n")
        return 0

    # args.format == "both"
    if args.format == "both":
        if args.output is None:
            raise SystemExit("--output must be provided when using --format both")

        target_dir = args.output
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "share-and-tell.json").write_text(json_output, encoding="utf-8")
        (target_dir / "share-and-tell.html").write_text(html_output, encoding="utf-8")
        return 0

    # args.format == "all"
    if args.output is None:
        raise SystemExit("--output must be provided when using --format all")

    target_dir = args.output
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "share-and-tell.json").write_text(json_output, encoding="utf-8")
    (target_dir / "share-and-tell.html").write_text(html_output, encoding="utf-8")
    (target_dir / "share-and-tell.csv").write_text(csv_output, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
