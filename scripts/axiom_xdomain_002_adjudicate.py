#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"
DEFAULT_EVENTS_FILE = EXP / "cross_domain_events.json"
DEFAULT_NULL_RESULTS_FILE = EXP / "null_results.json"
DEFAULT_OUT_FILE = EXP / "adjudication_draft.json"

PREDICTION_DOMAINS = {"cognitive", "computational"}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_utc(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(microsecond=0)


def fmt_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_events(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if "events" not in data or not isinstance(data["events"], list):
        raise SystemExit("cross_domain_events.json must contain an events array")
    return data


def load_logged_outcomes(path):
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = (
            data.get("null_results")
            or data.get("results")
            or data.get("outcomes")
            or data.get("records")
            or []
        )
    else:
        rows = []

    index = {}

    for row in rows:
        if not isinstance(row, dict):
            continue

        rid = (
            row.get("prediction_id")
            or row.get("record_id")
            or row.get("event_id")
            or row.get("id")
        )

        if not rid:
            continue

        outcome = str(row.get("outcome", "")).lower().strip()
        if not outcome:
            outcome = str(row.get("classification", "")).lower().strip()

        index[rid] = {
            "record_id": rid,
            "outcome": outcome,
            "reason": row.get("reason") or row.get("notes") or "Logged outcome override.",
            "raw": row
        }

    return index


def get_window_hours(event):
    if "prediction_window_hours" in event:
        try:
            return int(event["prediction_window_hours"])
        except Exception:
            pass

    output = event.get("output_json")
    if isinstance(output, dict) and "prediction_window_hours" in output:
        try:
            return int(output["prediction_window_hours"])
        except Exception:
            pass

    return 72


def get_topics(event):
    if isinstance(event.get("topic_tags"), list):
        return event["topic_tags"]

    output = event.get("output_json")
    if isinstance(output, dict) and isinstance(output.get("expected_topics"), list):
        return output["expected_topics"]

    return []


def is_fallback(event):
    output = event.get("output_json")
    if not isinstance(output, dict):
        return False
    notes = str(output.get("notes", "")).lower()
    return "fallback json" in notes or "parse/error" in notes


def provisional_prediction_record(event, as_of, logged_outcomes):
    event_id = event.get("event_id")
    domain = event.get("domain")
    timestamp = parse_utc(event.get("timestamp_utc"))
    window_hours = get_window_hours(event)

    window_start = timestamp
    window_end = timestamp + timedelta(hours=window_hours) if timestamp else None

    fallback = is_fallback(event)
    logged = logged_outcomes.get(event_id)

    if logged and logged.get("outcome") == "excluded":
        provisional_outcome = "excluded"
        outcome_status = "logged_exclusion"
        valid_for_matching = False
        reason = f"Logged exclusion: {logged.get('reason')}"
    elif logged and logged.get("outcome") in {"null", "miss", "ambiguous"}:
        provisional_outcome = logged["outcome"]
        outcome_status = "logged_outcome"
        valid_for_matching = logged["outcome"] != "ambiguous" and timestamp is not None
        reason = f"Logged outcome: {logged.get('reason')}"
    elif fallback:
        provisional_outcome = "excluded"
        outcome_status = "provisional"
        valid_for_matching = False
        reason = "Fallback/generated recovery output; preserve but exclude from scoring."
    elif window_end is None:
        provisional_outcome = "ambiguous"
        outcome_status = "provisional"
        valid_for_matching = False
        reason = "Missing or invalid timestamp; cannot compute outcome window."
    elif as_of < window_end:
        provisional_outcome = "null"
        outcome_status = "provisional_open_window"
        valid_for_matching = True
        reason = "Outcome window is still open; no hit/miss adjudication performed."
    else:
        provisional_outcome = "null"
        outcome_status = "provisional_closed_unmatched"
        valid_for_matching = True
        reason = "Outcome window is closed, but physical event matching is not enabled in this bridge."

    return {
        "record_id": event_id,
        "record_type": domain,
        "raw_file": event.get("raw_file"),
        "timestamp_utc": fmt_utc(timestamp),
        "window_hours": window_hours,
        "window_start_utc": fmt_utc(window_start),
        "window_end_utc": fmt_utc(window_end),
        "window_closed_as_of": bool(window_end and as_of >= window_end),
        "topics": get_topics(event),
        "valid_for_matching": bool(valid_for_matching),
        "fallback_generated": fallback,
        "logged_outcome_applied": bool(logged),
        "provisional_outcome": provisional_outcome,
        "outcome_status": outcome_status,
        "matched_event_ids": [],
        "reason": reason
    }


def physical_event_record(event):
    return {
        "event_id": event.get("event_id"),
        "record_type": "physical",
        "timestamp_utc": event.get("timestamp_utc"),
        "ingested_at_utc": event.get("ingested_at_utc"),
        "source_tier": event.get("source_tier"),
        "confidence": event.get("confidence"),
        "event_type": event.get("event_type"),
        "topic_tags": event.get("topic_tags", []),
        "source_reference": event.get("source_reference"),
        "independence_group": event.get("independence_group"),
        "contamination_risk": event.get("contamination_risk"),
        "negative_null": event.get("negative_null"),
        "prediction_reference_used": event.get("prediction_reference_used", None),
        "adjudication_status": "available_for_future_matching",
        "matched_prediction_ids": []
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create a non-scoring adjudication draft for AXIOM-XDOMAIN-002."
    )
    parser.add_argument("--events-file", default=str(DEFAULT_EVENTS_FILE))
    parser.add_argument("--null-results-file", default=str(DEFAULT_NULL_RESULTS_FILE))
    parser.add_argument("--out", default=str(DEFAULT_OUT_FILE))
    parser.add_argument("--as-of-utc", default=None)
    args = parser.parse_args()

    events_file = Path(args.events_file)
    null_results_file = Path(args.null_results_file)
    out_path = Path(args.out)

    as_of = parse_utc(args.as_of_utc) if args.as_of_utc else utc_now()
    data = load_events(events_file)
    logged_outcomes = load_logged_outcomes(null_results_file)

    prediction_records = []
    physical_records = []
    other_records = []

    for event in data["events"]:
        domain = event.get("domain")

        if domain in PREDICTION_DOMAINS:
            prediction_records.append(provisional_prediction_record(event, as_of, logged_outcomes))
        elif domain == "physical":
            physical_records.append(physical_event_record(event))
        else:
            other_records.append({
                "event_id": event.get("event_id"),
                "domain": domain,
                "status": "unknown_domain_preserved"
            })

    summary = {
        "study_id": "AXIOM-XDOMAIN-002",
        "generated_utc": fmt_utc(utc_now()),
        "as_of_utc": fmt_utc(as_of),
        "adjudication_stage": "bridge_no_physical_matching_no_scoring",
        "n_prediction_records": len(prediction_records),
        "n_physical_records": len(physical_records),
        "n_other_records": len(other_records),
        "n_logged_outcome_overrides": sum(1 for r in prediction_records if r["logged_outcome_applied"]),
        "n_windows_open": sum(1 for r in prediction_records if r["outcome_status"] == "provisional_open_window"),
        "n_windows_closed_unmatched": sum(1 for r in prediction_records if r["outcome_status"] == "provisional_closed_unmatched"),
        "n_excluded": sum(1 for r in prediction_records if r["provisional_outcome"] == "excluded"),
        "scoring_performed": False,
        "physical_matching_performed": False
    }

    output = {
        "study_id": "AXIOM-XDOMAIN-002",
        "record_type": "adjudication_draft",
        "source_policy": "derived_from_committed_event_ledger_no_raw_mutation",
        "summary": summary,
        "prediction_records": prediction_records,
        "physical_records": physical_records,
        "other_records": other_records
    }

    out_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
