#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"

RAW_COG = EXP / "raw" / "cognitive"
RAW_COMP = EXP / "raw" / "computational"
EVENTS_FILE = EXP / "cross_domain_events.json"
NULL_FILE = EXP / "null_results.json"
OUT_FILE = EXP / "scores.json"


def parse_time(t):
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


def timing_score(pred_time, event_time, window_hours):
    if not event_time:
        return 0.5
    delta = (event_time - pred_time).total_seconds() / 3600
    if delta < 0:
        return 0.0
    return max(0.1, 1.0 - (delta / window_hours))


def independence_score(group_size):
    return 1.0 / max(1, group_size)


def load_raw_predictions():
    preds = []

    for folder in [RAW_COG, RAW_COMP]:
        if not folder.exists():
            continue

        for f in folder.glob("*.txt"):
            try:
                content = f.read_text()
                preds.append({
                    "id": f.stem,
                    "raw": content,
                    "timestamp_utc": extract_timestamp(f.stem),
                    "prediction_window_hours": 72,
                    "specificity": 0.85,
                    "confidence": 0.65,
                    "contamination_risk": 0.15,
                    "independence_group_size": 1
                })
            except Exception:
                continue

    return preds


def extract_timestamp(pid):
    # C_002_20260501_080311 → extract timestamp
    parts = pid.split("_")
    if len(parts) < 4:
        return None

    ts = parts[2] + parts[3]
    return datetime.strptime(ts, "%Y%m%d%H%M%S")


def load_events():
    if not EVENTS_FILE.exists():
        return []
    return json.loads(EVENTS_FILE.read_text()).get("events", [])


def load_nulls():
    if not NULL_FILE.exists():
        return []
    return json.loads(NULL_FILE.read_text()).get("nulls", [])


def classify_outcome(pred, events):
    # VERY SIMPLE placeholder logic
    # You will refine this later

    for e in events:
        if any(tag in e.get("event_type", "") for tag in ["spectroscopy", "water", "isotope"]):
            return "hit", parse_time(e["timestamp_utc"])

    return "null", None


def compute_score(p):
    if p["outcome"] == "excluded":
        return None

    base_map = {
        "hit": 1.0,
        "miss": -1.0,
        "null": 0.0,
        "ambiguous": 0.25
    }

    base = base_map[p["outcome"]]

    pred_time = p["timestamp_utc"]
    event_time = p.get("event_time")

    timing = timing_score(pred_time, event_time, p["prediction_window_hours"])
    independence = independence_score(p["independence_group_size"])

    score = (
        base *
        p["specificity"] *
        p["confidence"] *
        independence *
        (1 - p["contamination_risk"]) *
        timing
    )

    return round(score, 6)


def main():
    preds = load_raw_predictions()
    events = load_events()

    results = []
    total = 0
    count = 0

    for p in preds:
        outcome, event_time = classify_outcome(p, events)

        p["outcome"] = outcome
        p["event_time"] = event_time

        score = compute_score(p)

        if score is not None:
            total += score
            count += 1

        results.append({
            "prediction_id": p["id"],
            "outcome": outcome,
            "score": score
        })

    summary = {
        "n_scored": count,
        "total_score": round(total, 6),
        "mean_score": round(total / count, 6) if count else 0
    }

    output = {
        "summary": summary,
        "results": results
    }

    OUT_FILE.write_text(json.dumps(output, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
