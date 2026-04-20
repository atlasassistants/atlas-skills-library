from __future__ import annotations

import argparse
import sys

from profile_paths import PROFILE_TEMPLATE_MAP, bootstrap_runtime_profiles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize live client-profile files from tracked templates.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing live runtime files from templates.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the files that would be created or overwritten.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(PROFILE_TEMPLATE_MAP.keys()),
        help="Limit initialization to specific runtime files.",
    )
    return parser


def _print_group(label: str, items: list[str]) -> None:
    if not items:
        return
    print(f"{label}: {', '.join(items)}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = bootstrap_runtime_profiles(
        force=args.force,
        dry_run=args.dry_run,
        names=args.only,
    )

    if args.dry_run:
        print("Dry run only. No files were changed.")

    _print_group("Created", result["created"])
    _print_group("Overwritten", result["overwritten"])
    _print_group("Skipped existing", result["skipped"])
    _print_group("Missing templates", result["missing_templates"])

    if not any(result.values()):
        print("Nothing to initialize.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
