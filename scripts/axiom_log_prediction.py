#!/usr/bin/env python3
import json, hashlib, argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("experiments/axiom_xdomain_001")
RAW = ROOT / "raw"
EVENTS = ROOT / "cross_domain_events.json"

RAW.mkdir(parents=True, exist_ok=True)

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_events():
    if EVENTS.exists():
        return json.loads(EVENTS.read_text())
    return {"study_id": "AXIOM-XDOMAIN-001", "version": "live", "events": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True, help="Specific prediction text")
    p.add_argument("--window-hours", type=int, default=72)
    p.add_argument("--specificity", type=float, default=0.8)
    p.add_argument("--confidence", type=float, default=0.7)
    p.add_argument("--anomaly-score", type=float, default=0.7)
    args = p.parse_args()

    ts = utc_now()
    event_id = "C_live_" + ts.replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")

    raw_text = "\n".join([
        f"event_id={event_id}",
        f"timestamp_utc={ts}",
        f"text={args.text}",
        f"window_hours={args.window_hours}",
        "locked_before_outcome=true",
        "hash_created_before_outcome=true",
        "study_id=AXIOM-XDOMAIN-001"
    ])

    raw_path = RAW / f"{event_id}.txt"
    raw_path.write_text(raw_text)
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
        "locked_before_outcome": True,
        "raw_file": str(raw_path.relative_to(ROOT)),
        "raw_hash_sha256": f"sha256:{digest}",
        "hash_method": "sha256_raw_file_v1",
        "hash_created_before_outcome": True,
        "independence_group": "live_user_prediction",
        "contamination_risk": 0.15,
        "negative_null": False
    })

    EVENTS.write_text(json.dumps(data, indent=2))
    print(json.dumps({"created": event_id, "timestamp_utc": ts, "hash": f"sha256:{digest}"}, indent=2))

if __name__ == "__main__":
    main()
