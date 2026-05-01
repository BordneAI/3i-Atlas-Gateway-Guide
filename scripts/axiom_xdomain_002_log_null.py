#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("experiments/axiom_xdomain_002")
NULLS = ROOT / "null_results.json"

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_nulls():
    if NULLS.exists():
        return json.loads(NULLS.read_text())
    return {"study_id": "AXIOM-XDOMAIN-002", "null_results": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prediction-id", required=True)
    p.add_argument("--window-start-utc", required=True)
    p.add_argument("--window-end-utc", required=True)
    p.add_argument("--outcome", required=True, choices=["matched", "unmatched", "ambiguous", "excluded"])
    p.add_argument("--reason", required=True)
    p.add_argument("--notes", default="")
    args = p.parse_args()

    data = load_nulls()
    data.setdefault("null_results", []).append({
        "prediction_id": args.prediction_id,
        "logged_utc": utc_now(),
        "window_start_utc": args.window_start_utc,
        "window_end_utc": args.window_end_utc,
        "outcome": args.outcome,
        "reason": args.reason,
        "negative_null": args.outcome in ["unmatched", "ambiguous"],
        "notes": args.notes
    })

    NULLS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"logged": args.prediction_id, "outcome": args.outcome}, indent=2))

if __name__ == "__main__":
    main()
