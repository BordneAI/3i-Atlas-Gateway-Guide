#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("experiments/axiom_xdomain_002")
RAW = ROOT / "raw" / "computational"
EVENTS = ROOT / "cross_domain_events.json"
RAW.mkdir(parents=True, exist_ok=True)

FIXED_PROMPT = "Assess whether any current 3I/ATLAS-related scientific release is likely within the next 72 hours. Classify expected domain tags only. Do not browse. Do not use new external information. Output fixed JSON only."

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
    p.add_argument("--output-json", required=True, help="Fixed JSON output from Axiom/Gateway")
    p.add_argument("--confidence", type=float, default=0.7)
    p.add_argument("--anomaly-score", type=float, default=0.7)
    args = p.parse_args()

    ts = utc_now()
    event_id = "K_002_" + ts.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")

    parsed_output = json.loads(args.output_json)

    raw_text = "\n".join([
        f"event_id={event_id}",
        f"timestamp_utc={ts}",
        "prompt_id=AXIOM-XDOMAIN-002-FIXED-PROMPT-001",
        f"prompt={FIXED_PROMPT}",
        f"output_json={json.dumps(parsed_output, sort_keys=True)}",
        "hash_created_before_outcome=true",
        "study_id=AXIOM-XDOMAIN-002"
    ])

    raw_path = RAW / f"{event_id}.txt"
    raw_path.write_text(raw_text, encoding="utf-8")
    digest = sha256_file(raw_path)

    data = load_events()
    data.setdefault("events", []).append({
        "event_id": event_id,
        "domain": "computational",
        "timestamp_utc": ts,
        "system": "Axiom/Gateway",
        "prompt_id": "AXIOM-XDOMAIN-002-FIXED-PROMPT-001",
        "model_or_runtime_version": "v2.15.0-candidate",
        "output_json": parsed_output,
        "tier": "T3",
        "confidence": args.confidence,
        "anomaly_score": args.anomaly_score,
        "hash_created_before_outcome": True,
        "raw_file": str(raw_path.relative_to(ROOT)),
        "raw_hash_sha256": f"sha256:{digest}",
        "hash_method": "sha256_raw_file_v1",
        "independence_group": "scheduled_computational_run",
        "contamination_risk": 0.15,
        "negative_null": False
    })

    EVENTS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"created": event_id, "timestamp_utc": ts, "hash": f"sha256:{digest}"}, indent=2))

if __name__ == "__main__":
    main()
