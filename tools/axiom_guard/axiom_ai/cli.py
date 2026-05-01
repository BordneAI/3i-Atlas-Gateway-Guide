"""Command line interface for Axiom Guard."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .audit import LocalLedger
from .classifier import DEFAULT_SMOKE_INPUT, classify_claim


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Axiom Guard bounded claim classifier")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plain", action="store_true", help="print key-value output")
    mode.add_argument("--json", action="store_true", help="print JSON output")
    parser.add_argument("--no-persist", action="store_true", help="disable audit and memory persistence")
    parser.add_argument("--text", help="claim text to classify")
    return parser


def read_input(explicit_text: str | None) -> str:
    if explicit_text:
        return explicit_text
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            return piped
    return DEFAULT_SMOKE_INPUT


def render_plain(payload: dict[str, object]) -> str:
    result = payload["result"]
    assert isinstance(result, dict)
    lines = [
        f"classification: {result['classification']}",
        f"detection_status: {result['detection_status']}",
        f"confidence: {result['confidence']}",
        f"proof_of_absence: {str(result['proof_of_absence']).lower()}",
        f"aaiv_policy: {result['aaiv_policy']}",
        f"claim: {result['claim']}",
    ]
    notes = result.get("governance_notes", [])
    if isinstance(notes, list):
        for note in notes:
            lines.append(f"note: {note}")
    lines.append(f"persisted: {str(payload.get('persisted', False)).lower()}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = classify_claim(read_input(args.text))
    ledger = LocalLedger(persist=not args.no_persist)
    audit_entry = ledger.record(result.to_dict())
    payload = {
        "tool": "Axiom Guard",
        "tool_version": "0.2.1",
        "mode": "json" if args.json else "plain",
        "persisted": bool(audit_entry.get("persisted")),
        "result": result.to_dict(),
    }

    if args.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_plain(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

