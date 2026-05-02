#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"

RAW_COMP = EXP / "raw" / "computational"
EVENTS_FILE = EXP / "cross_domain_events.json"
SCORES_FILE = EXP / "scores.json"
ADJUDICATION_FILE = EXP / "adjudication_draft.json"
VALIDATOR = ROOT / "scripts" / "axiom_xdomain_002_validate_events.py"


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_utc(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(microsecond=0)
    except Exception:
        return None


def fmt_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def parse_kv_file(path):
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def run_validator():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        return {
            "status": "fail",
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    try:
        payload = json.loads(result.stdout)
    except Exception as exc:
        return {
            "status": "fail",
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "parse_error": str(exc),
        }

    return {
        "status": payload.get("status", "fail"),
        "n_events": payload.get("n_events"),
        "domain_counts": payload.get("domain_counts", {}),
        "n_errors": payload.get("n_errors"),
        "n_warnings": payload.get("n_warnings"),
    }


def severity_rank(status):
    return {"pass": 0, "warn": 1, "fail": 2}.get(status, 2)


def add_check(checks, name, status, message, **data):
    checks.append({
        "name": name,
        "status": status,
        "message": message,
        **data,
    })


def latest_computational_file():
    files = sorted(RAW_COMP.glob("K_002_*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def event_ids_from_ledger(events_data):
    if not isinstance(events_data, dict):
        return set()
    events = events_data.get("events", [])
    if not isinstance(events, list):
        return set()
    return {e.get("event_id") for e in events if isinstance(e, dict)}


def raw_files_from_scores(scores_data):
    if not isinstance(scores_data, dict):
        return set()
    results = scores_data.get("results", [])
    if not isinstance(results, list):
        return set()
    return {r.get("raw_file") for r in results if isinstance(r, dict)}


def record_ids_from_adjudication(adjudication_data):
    if not isinstance(adjudication_data, dict):
        return set()
    records = adjudication_data.get("prediction_records", [])
    if not isinstance(records, list):
        return set()
    return {r.get("record_id") for r in records if isinstance(r, dict)}


def main():
    parser = argparse.ArgumentParser(
        description="Health-check AXIOM-XDOMAIN-002 cadence, ledger, scoring, and adjudication state."
    )
    parser.add_argument("--warn-age-hours", type=float, default=13.0)
    parser.add_argument("--fail-age-hours", type=float, default=15.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks = []
    generated = now_utc()

    latest_file = latest_computational_file()
    latest = {
        "file": None,
        "event_id": None,
        "timestamp_utc": None,
        "age_hours": None,
    }

    if latest_file is None:
        add_check(checks, "latest_computational_output", "fail", "No computational output files found.")
    else:
        kv = parse_kv_file(latest_file)
        latest["file"] = str(latest_file.relative_to(ROOT))
        latest["event_id"] = kv.get("event_id")
        latest["timestamp_utc"] = kv.get("timestamp_utc")

        ts = parse_utc(kv.get("timestamp_utc"))
        if ts is None:
            add_check(checks, "latest_computational_timestamp", "fail", "Latest computational output has invalid timestamp.", file=latest["file"])
        else:
            age_hours = (generated - ts).total_seconds() / 3600
            latest["age_hours"] = round(age_hours, 3)

            if age_hours < -0.01:
                add_check(checks, "latest_computational_age", "warn", "Latest computational output timestamp is in the future.", age_hours=latest["age_hours"])
            elif age_hours >= args.fail_age_hours:
                add_check(checks, "latest_computational_age", "fail", "Latest computational output is stale.", age_hours=latest["age_hours"], fail_age_hours=args.fail_age_hours)
            elif age_hours >= args.warn_age_hours:
                add_check(checks, "latest_computational_age", "warn", "Latest computational output is approaching stale threshold.", age_hours=latest["age_hours"], warn_age_hours=args.warn_age_hours)
            else:
                add_check(checks, "latest_computational_age", "pass", "Latest computational output is fresh.", age_hours=latest["age_hours"])

        if latest["event_id"]:
            add_check(checks, "latest_computational_event_id", "pass", "Latest computational output has event_id.", event_id=latest["event_id"])
        else:
            add_check(checks, "latest_computational_event_id", "fail", "Latest computational output is missing event_id.", file=latest["file"])

    validator_result = run_validator()
    if validator_result.get("status") == "pass":
        add_check(checks, "event_ledger_validator", "pass", "cross_domain_events.json validator passed.", validator=validator_result)
    else:
        add_check(checks, "event_ledger_validator", "fail", "cross_domain_events.json validator failed.", validator=validator_result)

    events_data = load_json(EVENTS_FILE)
    if events_data is None:
        add_check(checks, "event_ledger_exists", "fail", "cross_domain_events.json is missing.")
    else:
        add_check(checks, "event_ledger_exists", "pass", "cross_domain_events.json exists.")
        if latest["event_id"]:
            ledger_ids = event_ids_from_ledger(events_data)
            if latest["event_id"] in ledger_ids:
                add_check(checks, "latest_output_in_event_ledger", "pass", "Latest computational event is present in event ledger.")
            else:
                add_check(checks, "latest_output_in_event_ledger", "fail", "Latest computational event is missing from event ledger.", event_id=latest["event_id"])

    scores_data = load_json(SCORES_FILE)
    if scores_data is None:
        add_check(checks, "scores_file_exists", "fail", "scores.json is missing.")
    else:
        summary = scores_data.get("summary", {})
        add_check(
            checks,
            "scores_file_exists",
            "pass",
            "scores.json exists.",
            summary={
                "n_records": summary.get("n_records"),
                "n_scored": summary.get("n_scored"),
                "n_excluded": summary.get("n_excluded"),
                "total_score": summary.get("total_score"),
                "mean_score": summary.get("mean_score"),
            },
        )

        if latest["file"]:
            scored_raw_files = raw_files_from_scores(scores_data)
            raw_rel = latest["file"].replace("experiments/axiom_xdomain_002/", "")
            if raw_rel in scored_raw_files:
                add_check(checks, "latest_output_in_scores", "pass", "Latest computational output is represented in scores.json.")
            else:
                add_check(checks, "latest_output_in_scores", "warn", "Latest computational output is not represented in scores.json; rerun normalization/scoring.", raw_file=raw_rel)

    adjudication_data = load_json(ADJUDICATION_FILE)
    if adjudication_data is None:
        add_check(checks, "adjudication_file_exists", "fail", "adjudication_draft.json is missing.")
    else:
        summary = adjudication_data.get("summary", {})
        add_check(
            checks,
            "adjudication_file_exists",
            "pass",
            "adjudication_draft.json exists.",
            summary={
                "n_prediction_records": summary.get("n_prediction_records"),
                "n_physical_records": summary.get("n_physical_records"),
                "n_excluded": summary.get("n_excluded"),
                "scoring_performed": summary.get("scoring_performed"),
                "physical_matching_performed": summary.get("physical_matching_performed"),
            },
        )

        if summary.get("scoring_performed") is False:
            add_check(checks, "adjudication_no_scoring", "pass", "Adjudication bridge correctly reports no scoring.")
        else:
            add_check(checks, "adjudication_no_scoring", "fail", "Adjudication draft unexpectedly reports scoring performed.")

        if summary.get("physical_matching_performed") is False:
            add_check(checks, "adjudication_no_physical_matching", "pass", "Adjudication bridge correctly reports no physical matching.")
        else:
            add_check(checks, "adjudication_no_physical_matching", "fail", "Adjudication draft unexpectedly reports physical matching performed.")

        if latest["event_id"]:
            adjudicated_ids = record_ids_from_adjudication(adjudication_data)
            if latest["event_id"] in adjudicated_ids:
                add_check(checks, "latest_output_in_adjudication", "pass", "Latest computational output is represented in adjudication draft.")
            else:
                add_check(checks, "latest_output_in_adjudication", "warn", "Latest computational output is not represented in adjudication draft; rerun adjudication.", event_id=latest["event_id"])

    status = "pass"
    if any(c["status"] == "fail" for c in checks):
        status = "fail"
    elif any(c["status"] == "warn" for c in checks):
        status = "warn"

    output = {
        "study_id": "AXIOM-XDOMAIN-002",
        "generated_utc": fmt_utc(generated),
        "status": status,
        "latest_computational_output": latest,
        "checks": checks,
        "summary": {
            "n_checks": len(checks),
            "n_pass": sum(1 for c in checks if c["status"] == "pass"),
            "n_warn": sum(1 for c in checks if c["status"] == "warn"),
            "n_fail": sum(1 for c in checks if c["status"] == "fail"),
        },
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"status: {status}")
        print(f"latest: {latest.get('file')} at {latest.get('timestamp_utc')} age_hours={latest.get('age_hours')}")
        for check in checks:
            print(f"[{check['status']}] {check['name']}: {check['message']}")

    if status == "fail":
        sys.exit(1)


if __name__ == "__main__":
    main()
