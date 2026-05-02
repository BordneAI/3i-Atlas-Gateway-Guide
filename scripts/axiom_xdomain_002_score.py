#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"

EVENTS_FILE = EXP / "cross_domain_events.json"
NULL_FILE = EXP / "null_results.json"
NORM_COMP_FILE = EXP / "normalized_computational_events.json"
OUT_FILE = EXP / "scores.json"

def parse_time(t):
    if not t:
        return None
    return datetime.fromisoformat(t.replace("Z", "+00:00"))

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())

def timing_score(pred_time, event_time, window_hours):
    if not event_time:
        return 0.5
    delta = (event_time - pred_time).total_seconds() / 3600
    if delta < 0:
        return 0.0
    return max(0.1, 1.0 - (delta / window_hours))

def broadness_penalty(topic_count):
    if topic_count <= 2:
        return 1.0
    if topic_count == 3:
        return 0.90
    if topic_count == 4:
        return 0.80
    return 0.65

def outcome_base(outcome):
    return {
        "hit": 1.0,
        "miss": -1.0,
        "null": 0.0,
        "ambiguous": 0.25,
        "excluded": None
    }[outcome]

def load_events():
    return load_json(EVENTS_FILE, {"events": []}).get("events", [])

def load_null_results():
    return load_json(NULL_FILE, {"null_results": []}).get("null_results", [])

def load_computational_records():
    data = load_json(NORM_COMP_FILE, {"records": []})
    return data.get("records", [])

def classify_computational(record, nulls):
    if not record.get("valid_prediction", False):
        return "excluded", "Fallback/generated recovery output; not scored as model prediction."

    # Until physical/publication event matching exists, scheduled baseline remains null.
    return "null", "No qualifying physical/publication event adjudicated yet."

def compute_score(record, outcome):
    base = outcome_base(outcome)
    if base is None:
        return None

    pred_time = parse_time(record.get("timestamp_utc"))
    window_hours = int(record.get("prediction_window_hours", 72))
    confidence = float(record.get("confidence", 0.0))
    contamination = 0.15
    independence = 1.0
    topics = record.get("expected_topics", [])
    broadness = broadness_penalty(len(topics))

    score = (
        base *
        confidence *
        independence *
        (1 - contamination) *
        broadness *
        timing_score(pred_time, None, window_hours)
    )

    return round(score, 6)

def main():
    records = load_computational_records()
    nulls = load_null_results()

    results = []
    total = 0.0
    scored = 0
    excluded = 0

    for r in records:
        outcome, reason = classify_computational(r, nulls)
        score = compute_score(r, outcome)

        if score is None:
            excluded += 1
        else:
            total += score
            scored += 1

        results.append({
            "event_id": r.get("event_id"),
            "record_type": "computational",
            "valid_prediction": r.get("valid_prediction"),
            "expected_topics": r.get("expected_topics", []),
            "confidence": r.get("confidence"),
            "outcome": outcome,
            "score": score,
            "reason": reason,
            "raw_file": r.get("raw_file")
        })

    output = {
        "study_id": "AXIOM-XDOMAIN-002",
        "generated_utc": now_utc(),
        "summary": {
            "n_records": len(records),
            "n_scored": scored,
            "n_excluded": excluded,
            "total_score": round(total, 6),
            "mean_score": round(total / scored, 6) if scored else 0.0
        },
        "results": results
    }

    OUT_FILE.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["summary"], indent=2))

if __name__ == "__main__":
    main()
