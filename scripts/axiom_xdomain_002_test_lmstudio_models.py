#!/usr/bin/env python3
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

BASE = "http://localhost:1111"
OUT = Path("experiments/axiom_xdomain_002/logs/lmstudio_model_test.jsonl")

PROMPT = """Return ONLY compact JSON. No markdown. No reasoning.

Schema:
{"expected_topics":["no-update"],"prediction_window_hours":72,"classification":"scheduled_control_run","confidence":0.0,"notes":"test"}
"""

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def http_json(method, path, payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def try_json(text):
    if not text:
        return None
    text = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return None

def main():
    models = http_json("GET", "/v1/models")["data"]
    OUT.parent.mkdir(parents=True, exist_ok=True)

    for m in models:
        model = m["id"]
        if "embedding" in model.lower():
            continue

        result = {
            "timestamp_utc": utc_now(),
            "model": model,
            "ok": False,
            "error": "",
            "parsed": None,
            "content_preview": "",
            "reasoning_preview": ""
        }

        try:
            resp = http_json("POST", "/v1/chat/completions", {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": PROMPT}
                ],
                "temperature": 0.0,
                "max_tokens": 160
            })
            msg = resp["choices"][0]["message"]
            content = msg.get("content", "") or ""
            reasoning = msg.get("reasoning_content", "") or ""

            parsed = try_json(content) or try_json(reasoning)
            result["ok"] = parsed is not None
            result["parsed"] = parsed
            result["content_preview"] = content[:300]
            result["reasoning_preview"] = reasoning[:300]
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"

        print(json.dumps(result, indent=2))
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")

if __name__ == "__main__":
    main()
