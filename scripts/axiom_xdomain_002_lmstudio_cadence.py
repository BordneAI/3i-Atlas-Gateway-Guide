#!/usr/bin/env python3
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

BASE = "http://localhost:1111"
MODEL_PREFERENCE = [
    "qwen/qwen3.6-35b-a3b",
    "google/gemma-4-e4b",
    "openai/gpt-oss-20b"
]

PROMPT = """Output ONLY valid JSON.

Task:
Assess whether any 3I/ATLAS-related public scientific release is likely within the next 72 hours.

Allowed topic tags:
spectroscopy, isotopes, water, nga, no-update

Rules:
- Do not browse.
- Do not cite sources.
- Do not infer from new external data.
- Use only general prior pattern expectations.
- Output JSON only.

Schema:
{
  "expected_topics": ["..."],
  "prediction_window_hours": 72,
  "classification": "scheduled_control_run",
  "confidence": 0.0,
  "notes": "..."
}
"""

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def http_json(method, path, payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

def ensure_server():
    try:
        return http_json("GET", "/v1/models")
    except Exception:
        subprocess.run(["lms", "server", "start", "--port", "1111"], check=False)
    return http_json("GET", "/v1/models")

def choose_model(models):
    ids = [m.get("id", "") for m in models.get("data", [])]
    for pref in MODEL_PREFERENCE:
        for mid in ids:
            if pref in mid or mid in pref:
                return mid
    if ids:
        return ids[0]
    raise RuntimeError("No LM Studio models available from /v1/models")

def ask_model(model):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a bounded scheduled computational baseline. Output JSON only."},
            {"role": "user", "content": PROMPT}
        ],
        "temperature": 0.0,
        "max_tokens": 300
    }
    resp = http_json("POST", "/v1/chat/completions", payload)
    content = resp["choices"][0]["message"]["content"].strip()
    return json.loads(content)

def main():
    root = Path(__file__).resolve().parents[1]
    log = root / "experiments" / "axiom_xdomain_002" / "logs" / "lmstudio_cadence.log"
    log.parent.mkdir(parents=True, exist_ok=True)

    models = ensure_server()
    model = choose_model(models)

    try:
        output = ask_model(model)
    except Exception as e:
        output = {
            "expected_topics": ["no-update"],
            "prediction_window_hours": 72,
            "classification": "scheduled_control_run",
            "confidence": 0.25,
            "notes": f"Fallback JSON due LM Studio parse/error: {type(e).__name__}"
        }

    output["lmstudio_model"] = model
    output["run_utc"] = utc_now()

    cmd = [
        "python3",
        "scripts/axiom_xdomain_002_log_computational.py",
        "--output-json", json.dumps(output, sort_keys=True),
        "--confidence", str(float(output.get("confidence", 0.65))),
        "--anomaly-score", "0.60"
    ]

    subprocess.run(cmd, cwd=root, check=True)

    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp_utc": utc_now(), "model": model, "output": output}) + "\n")

if __name__ == "__main__":
    main()
