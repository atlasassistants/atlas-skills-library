#!/usr/bin/env python3
"""Set explicit provenance for an Atlas label on a message.

Usage:
    python shared/scripts/set_label_source.py <message_id> <label_name> <plugin|manual|unknown>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SHARED_SCRIPTS = Path(__file__).resolve().parent
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from state_store import StateStore
from atlas_labels import is_atlas_label


def main() -> int:
    parser = argparse.ArgumentParser(description="Set explicit provenance for an Atlas label record")
    parser.add_argument("message_id")
    parser.add_argument("label_name")
    parser.add_argument("source", choices=["plugin", "manual", "unknown"])
    args = parser.parse_args()

    if not is_atlas_label(args.label_name):
        print(f"ERROR: not an Atlas label: {args.label_name}", file=sys.stderr)
        return 1

    store = StateStore()
    store.set_label_source(args.message_id, args.label_name, args.source)
    print(
        {
            "message_id": args.message_id,
            "label": args.label_name,
            "source": args.source,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
