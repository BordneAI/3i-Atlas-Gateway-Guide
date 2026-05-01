#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("experiments/axiom_xdomain_002")
EVENTS = ROOT / "cross_domain_events.json"

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_events():
    if EVENTS.exists():
        return json.loads(EVENTS.read_text())
    return {"study_id": "AXIOM-XDOMAIN-002", "version": "0.1-preregistered", "events": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-id", required=True)
    p.add_argument("--source-type", required=True, choices=["arxiv", "nasa", "jpl", "mpc", "iawn", "observatory", "archive"])
    p.add_argument("--description", required=True)
    p.add_argument("--url", default="")
    p.add_argument("--tier", default="T2", choices=["T1", "T2"])
    p.add_argument("--confidence", type=float, default=0.8)
    p.add_argument("--anomaly-score", type=float, default=0.75)
    p.add_argument("--topic-tags", default="")
    p.add_argument("--timestamp-utc", default=None)
    args = p.parse_args()

    ts = args.timestamp_utc or utc_now()
    event_id = "P_002_" + ts.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
    topic_tags = [x.strip() for x in args.topic_tags.split(",") if x.strip()]

    data = load_events()
    data.setdefault("events", []).append({
        "event_id": event_id,
        "domain": "physical",
        "timestamp_utc": ts,
        "source_type": args.source_type,
        "source_id": args.source_id,
        "url": args.url,
        "tier": args.tier,
        "confidence": args.confidence,
        "anomaly_score": args.anomaly_score,
        "topic_tags": topic_tags,
        "description": args.description,
        "explicit_or_inferred": "explicit",
        "independence_group": "external_science_publication",
        "contamination_risk": 0.05,
        "negative_null": "no " in args.description.lower() or "non-detection" in args.description.lower()
    })

    EVENTS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"created": event_id, "timestamp_utc": ts}, indent=2))

if __name__ == "__main__":
    main()
