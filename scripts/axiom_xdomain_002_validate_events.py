#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"
DEFAULT_EVENTS_FILE = EXP / "cross_domain_events.json"

VALID_TIERS = {"T1", "T2", "T3", "T4"}
VALID_DOMAINS = {"cognitive", "computational", "physical"}
SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")

DISALLOWED_PHYSICAL_KEYS = {
    "prediction_id",
    "prediction_ids",
    "matched_prediction_id",
    "matched_prediction_ids",
    "prediction_text",
    "matching_prediction",
    "score_target",
    "desired_outcome",
}


def parse_utc(value, path, errors):
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: timestamp must be a non-empty string")
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        errors.append(f"{path}: invalid UTC timestamp {value!r}: {exc}")
        return None

    if dt.tzinfo is None:
        errors.append(f"{path}: timestamp must include timezone or Z suffix")
        return None

    return dt.astimezone(timezone.utc)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to read JSON from {path}: {exc}")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def require(event, key, path, errors):
    if key not in event:
        errors.append(f"{path}: missing required field {key!r}")
        return None
    return event.get(key)


def validate_float_range(event, key, path, errors, required=True):
    if key not in event:
        if required:
            errors.append(f"{path}: missing required field {key!r}")
        return

    value = event.get(key)
    if not isinstance(value, (int, float)):
        errors.append(f"{path}.{key}: must be a number")
        return

    if not (0.0 <= float(value) <= 1.0):
        errors.append(f"{path}.{key}: must be between 0 and 1")


def validate_bool(event, key, path, errors, required=True):
    if key not in event:
        if required:
            errors.append(f"{path}: missing required field {key!r}")
        return

    if not isinstance(event.get(key), bool):
        errors.append(f"{path}.{key}: must be boolean")


def validate_string(event, key, path, errors, required=True):
    if key not in event:
        if required:
            errors.append(f"{path}: missing required field {key!r}")
        return

    if not isinstance(event.get(key), str) or not event.get(key).strip():
        errors.append(f"{path}.{key}: must be a non-empty string")


def validate_topic_tags(value, path, errors):
    if not isinstance(value, list) or not value:
        errors.append(f"{path}.topic_tags: must be a non-empty list")
        return

    for i, tag in enumerate(value):
        if not isinstance(tag, str) or not tag.strip():
            errors.append(f"{path}.topic_tags[{i}]: must be a non-empty string")


def validate_common(event, index, seen_ids, errors, warnings):
    path = f"events[{index}]"

    event_id = require(event, "event_id", path, errors)
    if isinstance(event_id, str):
        if event_id in seen_ids:
            errors.append(f"{path}.event_id: duplicate event_id {event_id!r}")
        seen_ids.add(event_id)
    else:
        errors.append(f"{path}.event_id: must be a string")

    domain = require(event, "domain", path, errors)
    if domain not in VALID_DOMAINS:
        errors.append(f"{path}.domain: must be one of {sorted(VALID_DOMAINS)}, got {domain!r}")

    parse_utc(event.get("timestamp_utc"), f"{path}.timestamp_utc", errors)

    validate_float_range(event, "confidence", path, errors, required=False)
    validate_float_range(event, "contamination_risk", path, errors, required=False)
    validate_bool(event, "negative_null", path, errors, required=False)

    if event.get("prediction_reference_used") is True:
        warnings.append(f"{path}: prediction_reference_used=true detected")


def validate_computational(event, index, errors, warnings):
    path = f"events[{index}]"

    required = [
        "event_id",
        "domain",
        "timestamp_utc",
        "system",
        "prompt_id",
        "model_or_runtime_version",
        "output_json",
        "tier",
        "confidence",
        "anomaly_score",
        "hash_created_before_outcome",
        "raw_file",
        "raw_hash_sha256",
        "hash_method",
        "independence_group",
        "contamination_risk",
        "negative_null",
    ]

    for key in required:
        require(event, key, path, errors)

    if event.get("tier") not in VALID_TIERS:
        errors.append(f"{path}.tier: must be one of {sorted(VALID_TIERS)}")

    if not isinstance(event.get("output_json"), dict):
        errors.append(f"{path}.output_json: must be an object")
    else:
        output = event["output_json"]
        if output.get("classification") != "scheduled_control_run":
            warnings.append(f"{path}.output_json.classification: unexpected value {output.get('classification')!r}")
        if "expected_topics" in output and not isinstance(output["expected_topics"], list):
            errors.append(f"{path}.output_json.expected_topics: must be a list when present")

    validate_float_range(event, "confidence", path, errors)
    validate_float_range(event, "anomaly_score", path, errors)
    validate_float_range(event, "contamination_risk", path, errors)
    validate_bool(event, "hash_created_before_outcome", path, errors)
    validate_bool(event, "negative_null", path, errors)

    raw_hash = event.get("raw_hash_sha256")
    if not isinstance(raw_hash, str) or not SHA256_RE.match(raw_hash):
        errors.append(f"{path}.raw_hash_sha256: must match sha256:<64 lowercase hex chars>")
    else:
        raw_file = event.get("raw_file")
        if isinstance(raw_file, str) and raw_file:
            raw_path = EXP / raw_file
            if not raw_path.exists():
                errors.append(f"{path}.raw_file: does not exist: {raw_file}")
            else:
                actual = sha256_file(raw_path)
                if actual != raw_hash:
                    errors.append(f"{path}.raw_hash_sha256: hash mismatch for {raw_file}")
        else:
            errors.append(f"{path}.raw_file: must be a non-empty string")


def validate_physical(event, index, errors, warnings):
    path = f"events[{index}]"

    required = [
        "event_id",
        "domain",
        "timestamp_utc",
        "ingested_at_utc",
        "source_tier",
        "confidence",
        "event_type",
        "topic_tags",
        "description",
        "source_reference",
        "independence_group",
        "contamination_risk",
        "negative_null",
        "prediction_reference_used",
        "ingestion_policy",
    ]

    for key in required:
        require(event, key, path, errors)

    if event.get("source_tier") not in VALID_TIERS:
        errors.append(f"{path}.source_tier: must be one of {sorted(VALID_TIERS)}")

    validate_float_range(event, "confidence", path, errors)
    validate_float_range(event, "contamination_risk", path, errors)
    validate_bool(event, "negative_null", path, errors)
    validate_bool(event, "prediction_reference_used", path, errors)

    parse_utc(event.get("ingested_at_utc"), f"{path}.ingested_at_utc", errors)

    validate_string(event, "event_type", path, errors)
    validate_string(event, "description", path, errors)
    validate_string(event, "source_reference", path, errors)
    validate_string(event, "independence_group", path, errors)
    validate_string(event, "ingestion_policy", path, errors)

    validate_topic_tags(event.get("topic_tags"), path, errors)

    if event.get("prediction_reference_used") is not False:
        errors.append(f"{path}.prediction_reference_used: physical events must set this to false")

    for key in DISALLOWED_PHYSICAL_KEYS:
        if key in event:
            errors.append(f"{path}: physical event must not include prediction-coupling key {key!r}")

    if event.get("source_reference") == "dry-run-local-test":
        errors.append(f"{path}.source_reference: dry-run test source must not be appended")


def validate_cognitive(event, index, errors, warnings):
    path = f"events[{index}]"

    required_basic = [
        "event_id",
        "domain",
        "timestamp_utc",
        "hash_created_before_outcome",
        "independence_group",
        "contamination_risk",
        "negative_null",
    ]

    for key in required_basic:
        require(event, key, path, errors)

    validate_bool(event, "hash_created_before_outcome", path, errors)
    validate_float_range(event, "contamination_risk", path, errors)
    validate_bool(event, "negative_null", path, errors)

    if "raw_hash_sha256" in event:
        raw_hash = event["raw_hash_sha256"]
        if not isinstance(raw_hash, str) or not SHA256_RE.match(raw_hash):
            errors.append(f"{path}.raw_hash_sha256: must match sha256:<64 lowercase hex chars>")

    if "raw_file" in event and "raw_hash_sha256" in event:
        raw_path = EXP / event["raw_file"]
        if raw_path.exists():
            actual = sha256_file(raw_path)
            if actual != event["raw_hash_sha256"]:
                errors.append(f"{path}.raw_hash_sha256: hash mismatch for {event['raw_file']}")
        else:
            warnings.append(f"{path}.raw_file: file not found for optional cognitive hash check")


def main():
    parser = argparse.ArgumentParser(
        description="Validate AXIOM-XDOMAIN-002 cross_domain_events.json without modifying it."
    )
    parser.add_argument("--file", default=str(DEFAULT_EVENTS_FILE))
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args()

    path = Path(args.file)
    data = load_json(path)

    errors = []
    warnings = []

    if not isinstance(data, dict):
        raise SystemExit("events file must contain a JSON object")

    if data.get("study_id") != "AXIOM-XDOMAIN-002":
        warnings.append("top-level study_id is missing or not AXIOM-XDOMAIN-002")

    events = data.get("events")
    if not isinstance(events, list):
        errors.append("top-level 'events' must be a list")
        events = []

    seen_ids = set()
    domain_counts = {}

    for i, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"events[{i}]: must be an object")
            continue

        validate_common(event, i, seen_ids, errors, warnings)

        domain = event.get("domain")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        if domain == "computational":
            validate_computational(event, i, errors, warnings)
        elif domain == "physical":
            validate_physical(event, i, errors, warnings)
        elif domain == "cognitive":
            validate_cognitive(event, i, errors, warnings)

    summary = {
        "file": str(path),
        "study_id": data.get("study_id"),
        "n_events": len(events),
        "domain_counts": domain_counts,
        "n_errors": len(errors),
        "n_warnings": len(warnings),
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"status: {summary['status']}")
        print(f"events: {summary['n_events']}")
        print(f"errors: {summary['n_errors']}")
        print(f"warnings: {summary['n_warnings']}")
        if errors:
            print("\nErrors:")
            for e in errors:
                print(f"- {e}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"- {w}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
