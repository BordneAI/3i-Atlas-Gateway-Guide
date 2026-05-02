#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"
RAW = EXP / "raw" / "computational"
OUT = EXP / "normalized_computational_events.json"

def parse_kv(path):
    data = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data

def main():
    records = []

    for path in sorted(RAW.glob("K_002_*.txt")):
        kv = parse_kv(path)

        try:
            output = json.loads(kv.get("output_json", "{}"))
        except Exception:
            output = {}

        notes = output.get("notes", "")
        is_fallback = "Fallback JSON" in notes or "parse/error" in notes

        record = {
            "event_id": kv.get("event_id"),
            "timestamp_utc": kv.get("timestamp_utc"),
            "raw_file": str(path.relative_to(EXP)),
            "prompt_id": kv.get("prompt_id"),
            "classification": output.get("classification", "scheduled_control_run"),
            "expected_topics": output.get("expected_topics", []),
            "prediction_window_hours": output.get("prediction_window_hours", 72),
            "confidence": float(output.get("confidence", 0.0)),
            "lmstudio_model": output.get("lmstudio_model"),
            "run_utc": output.get("run_utc", kv.get("timestamp_utc")),
            "valid_prediction": not is_fallback,
            "fallback_generated": is_fallback,
            "notes": notes,
            "hash_created_before_outcome": kv.get("hash_created_before_outcome") == "true",
            "study_id": kv.get("study_id")
        }

        records.append(record)

    OUT.write_text(json.dumps({
        "study_id": "AXIOM-XDOMAIN-002",
        "record_type": "normalized_computational_events",
        "source_policy": "derived_from_raw_files_no_raw_mutation",
        "records": records
    }, indent=2) + "\n")

    print(json.dumps({
        "normalized": len(records),
        "output": str(OUT)
    }, indent=2))

if __name__ == "__main__":
    main()
