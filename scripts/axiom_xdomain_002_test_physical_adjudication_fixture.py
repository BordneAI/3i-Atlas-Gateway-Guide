#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"
LIVE_EVENTS = EXP / "cross_domain_events.json"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd):
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    return result.stdout


def main():
    live_before = sha256(LIVE_EVENTS)

    with tempfile.TemporaryDirectory(prefix="axiom_xdomain_002_adjudication_fixture_") as tmp:
        tmpdir = Path(tmp)
        fixture_events = tmpdir / "cross_domain_events_fixture.json"
        fixture_adjudication = tmpdir / "adjudication_fixture.json"

        fixture_events.write_text(LIVE_EVENTS.read_text(encoding="utf-8"), encoding="utf-8")

        append_output = run([
            sys.executable,
            "scripts/axiom_xdomain_002_add_physical.py",
            "--events-file",
            str(fixture_events),
            "--timestamp-utc",
            "2026-05-02T00:00:00Z",
            "--source-tier",
            "T3",
            "--confidence",
            "0.50",
            "--event-type",
            "fixture-test-event",
            "--topic-tags",
            "test,fixture",
            "--description",
            "Fixture-only physical event for adjudication bridge test; not part of live experiment ledger.",
            "--source-reference",
            "fixture-adjudication-local-test",
            "--contamination-risk",
            "0.0",
        ])

        validation_output = run([
            sys.executable,
            "scripts/axiom_xdomain_002_validate_events.py",
            "--file",
            str(fixture_events),
            "--json",
        ])

        adjudication_output = run([
            sys.executable,
            "scripts/axiom_xdomain_002_adjudicate.py",
            "--events-file",
            str(fixture_events),
            "--out",
            str(fixture_adjudication),
        ])

        validation = json.loads(validation_output)
        adjudication = json.loads(fixture_adjudication.read_text(encoding="utf-8"))
        summary = adjudication["summary"]

        live_after = sha256(LIVE_EVENTS)

        checks = {
            "validator_passed": validation.get("status") == "pass",
            "fixture_has_one_physical_event": validation.get("domain_counts", {}).get("physical") == 1,
            "adjudication_has_one_physical_record": summary.get("n_physical_records") == 1,
            "scoring_not_performed": summary.get("scoring_performed") is False,
            "physical_matching_not_performed": summary.get("physical_matching_performed") is False,
            "live_ledger_unchanged": live_before == live_after,
        }

        failed = [name for name, ok in checks.items() if not ok]

        result = {
            "status": "pass" if not failed else "fail",
            "checks": checks,
            "failed": failed,
            "validation_summary": {
                "n_events": validation.get("n_events"),
                "domain_counts": validation.get("domain_counts"),
                "n_errors": validation.get("n_errors"),
                "n_warnings": validation.get("n_warnings"),
            },
            "adjudication_summary": summary,
            "fixture_append_output": json.loads(append_output),
        }

        print(json.dumps(result, indent=2))

        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
