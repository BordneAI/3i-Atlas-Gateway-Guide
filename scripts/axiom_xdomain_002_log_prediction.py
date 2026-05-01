#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("experiments/axiom_xdomain_002")
RAW = ROOT / "raw" / "cognitive"
EVENTS = ROOT / "cross_domain_events.json"
RAW.mkdir(parents=True, exist_ok=True)

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_events():
    if EVENTS.exists():
        return json.loads(EVENTS.read_text())
    return {"study_id": "AXIOM-XDOMAIN-002", "version": "0.1-preregistered", "events": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--window-hours", type=int, default=72)
    p.add_argument("--specificity", type=float, default=0.8)
    p.add_argument("--confidence", type=float, default=0.7)
    p.add_argument("--anomaly-score", type=float, default=0.7)
    p.add_argument("--topic-tags", default="")
    args = p.parse_args()

    ts = utc_now()
    event_id = "C_002_" + ts.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
    topic_tags = [x.strip() for x in args.topic_tags.split(",") if x.strip()]

    raw_text = "\n".join([
        f"event_id={event_id}",
        f"timestamp_utc={ts}",
        f"text={args.text}",
        f"window_hours={args.window_hours}",
        f"specificity={args.specificity}",
        f"confidence={args.confidence}",
        f"anomaly_score={args.anomaly_score}",
        f"topic_tags={','.join(topic_tags)}",
        "locked_before_outcome=true",
        "hash_created_before_outcome=true",
        "study_id=AXIOM-XDOMAIN-002"
    ])

    raw_path = RAW / f"{event_id}.txt"
    raw_path.write_text(raw_text, encoding="utf-8")
    digest = sha256_file(raw_path)

    data = load_events()
    data.setdefault("events", []).append({
        "event_id": event_id,
        "domain": "cognitive",
        "timestamp_utc": ts,
        "report_type": "live_prediction",
        "text": args.text,
        "window_hours": args.window_hours,
        "specificity": args.specificity,
        "confidence": args.confidence,
        "anomaly_score": args.anomaly_score,
        "topic_tags": topic_tags,
        "locked_before_outcome": True,
        "hash_created_before_outcome": True,
        "raw_file": str(raw_path.relative_to(ROOT)),
        "raw_hash_sha256": f"sha256:{digest}",
        "hash_method": "sha256_raw_file_v1",
        "independence_group": "live_user_prediction",
        "contamination_risk": 0.10,
        "negative_null": False
    })

    EVENTS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"created": event_id, "timestamp_utc": ts, "hash": f"sha256:{digest}"}, indent=2))

if __name__ == "__main__":
    main()
