#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "axiom_xdomain_002"
DEFAULT_EVENTS_FILE = EXP / "cross_domain_events.json"

VALID_TIERS = {"T1", "T2", "T3", "T4"}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as e:
        raise SystemExit(f"Invalid timestamp_utc: {value} ({e})")
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:40] or "event"


def load_events(path):
    if not path.exists():
        return {
            "study_id": "AXIOM-XDOMAIN-002",
            "version": "0.1-preregistered",
            "events": []
        }

    data = json.loads(path.read_text(encoding="utf-8"))

    if "events" not in data or not isinstance(data["events"], list):
        raise SystemExit(f"{path} must contain an 'events' array")

    return data


def write_events(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def make_event_id(timestamp_utc, topic_tags, source_reference):
    seed = "|".join([
        timestamp_utc,
        ",".join(topic_tags),
        source_reference
    ])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    topic_slug = slugify(topic_tags[0] if topic_tags else "event")
    compact_time = timestamp_utc.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
    return f"P_002_{compact_time}_{topic_slug}_{digest}"


def validate_event(event):
    if event["source_tier"] not in VALID_TIERS:
        raise SystemExit(f"source_tier must be one of {sorted(VALID_TIERS)}")

    if not (0.0 <= event["confidence"] <= 1.0):
        raise SystemExit("confidence must be between 0 and 1")

    if not (0.0 <= event["contamination_risk"] <= 1.0):
        raise SystemExit("contamination_risk must be between 0 and 1")

    if not event["topic_tags"]:
        raise SystemExit("at least one topic tag is required")

    if not event["source_reference"].strip():
        raise SystemExit("source_reference is required")

    if not event["description"].strip():
        raise SystemExit("description is required")


def main():
    parser = argparse.ArgumentParser(
        description="Append an independent physical/cross-domain event for AXIOM-XDOMAIN-002."
    )

    parser.add_argument("--events-file", default=str(DEFAULT_EVENTS_FILE), help="Target event ledger. Defaults to live cross_domain_events.json.")
    parser.add_argument("--timestamp-utc", required=True, help="Event/publication timestamp in UTC ISO format")
    parser.add_argument("--source-tier", required=True, choices=sorted(VALID_TIERS))
    parser.add_argument("--confidence", required=True, type=float)
    parser.add_argument("--event-type", required=True, help="Short event type, e.g. spectroscopy, water, isotopes")
    parser.add_argument("--topic-tags", required=True, help="Comma-separated tags, e.g. spectroscopy,water")
    parser.add_argument("--description", required=True)
    parser.add_argument("--source-reference", required=True, help="URL, DOI, arXiv ID, MPC/JPL reference, etc.")
    parser.add_argument("--independence-group", default="physical_event_independent")
    parser.add_argument("--contamination-risk", default=0.05, type=float)
    parser.add_argument("--negative-null", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    events_file = Path(args.events_file)
    topic_tags = [t.strip().lower() for t in args.topic_tags.split(",") if t.strip()]
    timestamp_utc = parse_utc(args.timestamp_utc)
    ingested_at_utc = utc_now()

    event = {
        "event_id": make_event_id(timestamp_utc, topic_tags, args.source_reference),
        "domain": "physical",
        "timestamp_utc": timestamp_utc,
        "ingested_at_utc": ingested_at_utc,
        "source_tier": args.source_tier,
        "confidence": args.confidence,
        "event_type": args.event_type.strip().lower(),
        "topic_tags": topic_tags,
        "description": args.description.strip(),
        "source_reference": args.source_reference.strip(),
        "independence_group": args.independence_group.strip(),
        "contamination_risk": args.contamination_risk,
        "negative_null": bool(args.negative_null),
        "prediction_reference_used": False,
        "ingestion_policy": "independent_event_ingestion_no_prediction_reference"
    }

    validate_event(event)

    data = load_events(events_file)

    existing_ids = {e.get("event_id") for e in data["events"]}
    if event["event_id"] in existing_ids:
        raise SystemExit(f"Duplicate event_id: {event['event_id']}")

    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "would_append_to": str(events_file),
            "event": event
        }, indent=2))
        return

    data["events"].append(event)
    write_events(events_file, data)

    print(json.dumps({
        "appended": event["event_id"],
        "file": str(events_file),
        "timestamp_utc": event["timestamp_utc"],
        "source_tier": event["source_tier"],
        "topic_tags": event["topic_tags"]
    }, indent=2))


if __name__ == "__main__":
    main()
