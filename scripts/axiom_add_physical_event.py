#!/usr/bin/env python3
import json, argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("experiments/axiom_xdomain_001")
EVENTS = ROOT / "cross_domain_events.json"

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_events():
    if EVENTS.exists():
        return json.loads(EVENTS.read_text())
    return {"study_id": "AXIOM-XDOMAIN-001", "version": "live", "events": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-id", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--tier", default="T2")
    p.add_argument("--confidence", type=float, default=0.75)
    p.add_argument("--anomaly-score", type=float, default=0.75)
    p.add_argument("--timestamp-utc", default=None)
    args = p.parse_args()

    ts = args.timestamp_utc or utc_now()
    event_id = "P_live_" + ts.replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")

    data = load_events()
    data.setdefault("events", []).append({
        "event_id": event_id,
        "domain": "physical",
        "timestamp_utc": ts,
        "source_file": "external_publication_or_kb_update",
        "source_id": args.source_id,
        "tier": args.tier,
        "confidence": args.confidence,
        "anomaly_score": args.anomaly_score,
        "description": args.description,
        "explicit_or_inferred": "explicit",
        "independence_group": "external_science_publication",
        "contamination_risk": 0.05,
        "negative_null": "no " in args.description.lower() or "non-detection" in args.description.lower()
    })

    EVENTS.write_text(json.dumps(data, indent=2))
    print(json.dumps({"created": event_id, "timestamp_utc": ts}, indent=2))

if __name__ == "__main__":
    main()
