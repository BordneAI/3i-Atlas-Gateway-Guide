#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"

EVENTS_FILE = EXP / "cross_domain_events.json"
SCORES_FILE = EXP / "scores.json"
ADJUDICATION_FILE = EXP / "adjudication_draft.json"
SOURCE_ELIGIBILITY_FILE = EXP / "SOURCE_ELIGIBILITY.md"
REPORT_DIR = EXP / "reports"

SUMMARY_JSON = REPORT_DIR / "summary.json"
SUMMARY_MD = REPORT_DIR / "summary.md"

HEALTHCHECK = ROOT / "scripts" / "axiom_xdomain_002_healthcheck.py"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def run_healthcheck():
    if not HEALTHCHECK.exists():
        return {
            "status": "missing",
            "summary": {},
            "latest_computational_output": {},
            "checks": [],
            "error": "healthcheck script missing"
        }

    result = subprocess.run(
        [sys.executable, str(HEALTHCHECK), "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    try:
        payload = json.loads(result.stdout)
    except Exception:
        return {
            "status": "fail",
            "summary": {},
            "latest_computational_output": {},
            "checks": [],
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": "failed to parse healthcheck JSON"
        }

    payload["returncode"] = result.returncode
    if result.stderr.strip():
        payload["stderr"] = result.stderr.strip()

    return payload


def count_raw_files():
    cognitive_dir = EXP / "raw" / "cognitive"
    computational_dir = EXP / "raw" / "computational"

    return {
        "raw_cognitive_files": len(list(cognitive_dir.glob("C_002_*.txt"))) if cognitive_dir.exists() else 0,
        "raw_computational_files": len(list(computational_dir.glob("K_002_*.txt"))) if computational_dir.exists() else 0,
    }


def build_summary():
    events = load_json(EVENTS_FILE) or {}
    scores = load_json(SCORES_FILE) or {}
    adjudication = load_json(ADJUDICATION_FILE) or {}
    health = run_healthcheck()

    event_rows = events.get("events", []) if isinstance(events.get("events"), list) else []
    domain_counts = {}
    for event in event_rows:
        if isinstance(event, dict):
            domain = event.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    scores_summary = scores.get("summary", {}) if isinstance(scores, dict) else {}
    adjudication_summary = adjudication.get("summary", {}) if isinstance(adjudication, dict) else {}

    raw_counts = count_raw_files()

    physical_events = domain_counts.get("physical", 0)
    physical_matching_performed = bool(adjudication_summary.get("physical_matching_performed"))
    scoring_performed_by_adjudication = bool(adjudication_summary.get("scoring_performed"))

    interpretation = {
        "baseline_only": physical_events == 0,
        "physical_events_ingested": physical_events,
        "physical_matching_performed": physical_matching_performed,
        "scoring_performed_by_adjudication": scoring_performed_by_adjudication,
        "signal_conclusion": "none",
        "t2_candidate_assessment": "blocked",
        "plain_language": (
            "Current report is baseline-only. No physical events have been ingested, "
            "no physical matching has been performed, and no signal conclusion can be drawn yet."
        )
    }

    return {
        "study_id": "AXIOM-XDOMAIN-002",
        "record_type": "interim_experiment_summary",
        "generated_utc": utc_now(),
        "source_policy": "derived_report_no_raw_mutation",
        "files": {
            "events": str(EVENTS_FILE.relative_to(ROOT)),
            "scores": str(SCORES_FILE.relative_to(ROOT)),
            "adjudication": str(ADJUDICATION_FILE.relative_to(ROOT)),
            "source_eligibility": str(SOURCE_ELIGIBILITY_FILE.relative_to(ROOT)),
            "summary_json": str(SUMMARY_JSON.relative_to(ROOT)),
            "summary_md": str(SUMMARY_MD.relative_to(ROOT)),
        },
        "event_ledger": {
            "n_events": len(event_rows),
            "domain_counts": domain_counts,
        },
        "raw_files": raw_counts,
        "scoring": {
            "n_records": scores_summary.get("n_records"),
            "n_scored": scores_summary.get("n_scored"),
            "n_excluded": scores_summary.get("n_excluded"),
            "total_score": scores_summary.get("total_score"),
            "mean_score": scores_summary.get("mean_score"),
        },
        "adjudication": {
            "n_prediction_records": adjudication_summary.get("n_prediction_records"),
            "n_physical_records": adjudication_summary.get("n_physical_records"),
            "n_logged_outcome_overrides": adjudication_summary.get("n_logged_outcome_overrides"),
            "n_windows_open": adjudication_summary.get("n_windows_open"),
            "n_windows_closed_unmatched": adjudication_summary.get("n_windows_closed_unmatched"),
            "n_excluded": adjudication_summary.get("n_excluded"),
            "scoring_performed": adjudication_summary.get("scoring_performed"),
            "physical_matching_performed": adjudication_summary.get("physical_matching_performed"),
        },
        "healthcheck": {
            "status": health.get("status"),
            "latest_computational_output": health.get("latest_computational_output", {}),
            "summary": health.get("summary", {}),
        },
        "interpretation": interpretation,
        "limitations": [
            "No real physical/publication event has been appended to the live ledger yet.",
            "No physical event matching has been performed.",
            "No final hit/miss adjudication has been performed.",
            "Current score is baseline/null behavior and does not indicate positive or negative anomaly evidence.",
            "AXIOM-XDOMAIN outputs remain experimental/T3 unless separately adjudicated, reviewed, and promoted."
        ]
    }


def write_summary_json(summary):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_summary_md(summary):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    event_counts = summary["event_ledger"]["domain_counts"]
    scoring = summary["scoring"]
    adjudication = summary["adjudication"]
    health = summary["healthcheck"]
    interpretation = summary["interpretation"]

    lines = [
        "# AXIOM-XDOMAIN-002 Interim Summary",
        "",
        f"Generated UTC: {summary['generated_utc']}",
        "",
        "## Status",
        "",
        "- Report type: interim experiment summary",
        "- Source policy: derived report, no raw mutation",
        f"- Health-check status: {health.get('status')}",
        f"- Signal conclusion: {interpretation['signal_conclusion']}",
        f"- T2_candidate assessment: {interpretation['t2_candidate_assessment']}",
        "",
        "## Interpretation",
        "",
        interpretation["plain_language"],
        "",
        "## Event Ledger",
        "",
        f"- Total events: {summary['event_ledger']['n_events']}",
        f"- Cognitive events: {event_counts.get('cognitive', 0)}",
        f"- Computational events: {event_counts.get('computational', 0)}",
        f"- Physical events: {event_counts.get('physical', 0)}",
        "",
        "## Raw Files",
        "",
        f"- Raw cognitive files: {summary['raw_files']['raw_cognitive_files']}",
        f"- Raw computational files: {summary['raw_files']['raw_computational_files']}",
        "",
        "## Scoring Snapshot",
        "",
        f"- Records: {scoring.get('n_records')}",
        f"- Scored: {scoring.get('n_scored')}",
        f"- Excluded: {scoring.get('n_excluded')}",
        f"- Total score: {scoring.get('total_score')}",
        f"- Mean score: {scoring.get('mean_score')}",
        "",
        "## Adjudication Draft",
        "",
        f"- Prediction records: {adjudication.get('n_prediction_records')}",
        f"- Physical records: {adjudication.get('n_physical_records')}",
        f"- Logged outcome overrides: {adjudication.get('n_logged_outcome_overrides')}",
        f"- Open windows: {adjudication.get('n_windows_open')}",
        f"- Closed unmatched windows: {adjudication.get('n_windows_closed_unmatched')}",
        f"- Excluded records: {adjudication.get('n_excluded')}",
        f"- Scoring performed: {adjudication.get('scoring_performed')}",
        f"- Physical matching performed: {adjudication.get('physical_matching_performed')}",
        "",
        "## Latest Computational Output",
        "",
        f"- File: {health.get('latest_computational_output', {}).get('file')}",
        f"- Event ID: {health.get('latest_computational_output', {}).get('event_id')}",
        f"- Timestamp UTC: {health.get('latest_computational_output', {}).get('timestamp_utc')}",
        f"- Age hours: {health.get('latest_computational_output', {}).get('age_hours')}",
        "",
        "## Limitations",
        "",
    ]

    for item in summary["limitations"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Artifact Paths",
        "",
        f"- Events: `{summary['files']['events']}`",
        f"- Scores: `{summary['files']['scores']}`",
        f"- Adjudication draft: `{summary['files']['adjudication']}`",
        f"- Source eligibility: `{summary['files']['source_eligibility']}`",
        f"- Summary JSON: `{summary['files']['summary_json']}`",
        f"- Summary Markdown: `{summary['files']['summary_md']}`",
        "",
    ])

    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate AXIOM-XDOMAIN-002 interim summary report."
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    summary = build_summary()
    write_summary_json(summary)

    if not args.json_only:
        write_summary_md(summary)

    print(json.dumps({
        "generated": True,
        "status": "pass",
        "summary_json": str(SUMMARY_JSON.relative_to(ROOT)),
        "summary_md": None if args.json_only else str(SUMMARY_MD.relative_to(ROOT)),
        "signal_conclusion": summary["interpretation"]["signal_conclusion"],
        "physical_events": summary["event_ledger"]["domain_counts"].get("physical", 0),
        "physical_matching_performed": summary["adjudication"].get("physical_matching_performed"),
    }, indent=2))


if __name__ == "__main__":
    main()
