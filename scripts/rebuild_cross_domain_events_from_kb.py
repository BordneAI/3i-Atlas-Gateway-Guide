#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
OUT_DIR = ROOT / "experiments" / "axiom_xdomain_001"
RAW_DIR = OUT_DIR / "raw"
OUT_FILE = OUT_DIR / "cross_domain_events.json"

KB_FILE = ROOT / "knowledge_base_merged_v2.json"
SOURCES_FILE = ROOT / "sources.json"
CHANGELOG_FILE = ROOT / "kb_changelog.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def write_raw(event_id, text):
    path = RAW_DIR / f"{event_id}.txt"
    path.write_text(text, encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()

def confidence_to_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    mapping = {
        "extremely_high": 0.95,
        "high": 0.85,
        "medium_high": 0.75,
        "medium": 0.65,
        "low": 0.35,
        "extremely_low": 0.15
    }
    return mapping.get(str(value).lower(), 0.6)

def tier_weight(tier):
    return {
        "T1": 0.95,
        "T2": 0.80,
        "T3": 0.55,
        "T4": 0.25
    }.get(tier, 0.30)

def find_fact(kb, fact_id):
    for item in kb.get("facts", []):
        if item.get("id") == fact_id:
            return item
    return None

def make_physical_event(kb, fact_id, anomaly_score):
    fact = find_fact(kb, fact_id)
    if not fact:
        return None

    tier = fact.get("tier") or fact.get("truth_tier") or "Unknown"
    source_id = fact.get("source_id") or (fact.get("sources", [""])[0] if fact.get("sources") else "")

    return {
        "event_id": f"P_{fact_id}",
        "domain": "physical",
        "timestamp_utc": f"{fact.get('as_of', '1970-01-01')}T00:00:00Z" if len(str(fact.get("as_of", ""))) == 10 else str(fact.get("as_of", "1970-01-01T00:00:00Z")),
        "source_file": "knowledge_base_merged_v2.json",
        "source_id": source_id,
        "kb_fact_id": fact_id,
        "tier": tier,
        "confidence": confidence_to_float(fact.get("confidence", 0.6)),
        "anomaly_score": anomaly_score,
        "description": fact.get("summary") or fact.get("text") or "",
        "explicit_or_inferred": "explicit",
        "independence_group": "kb_physical_source",
        "contamination_risk": 0.10,
        "negative_null": "negative-null" in str(fact).lower() or "nondetection" in str(fact).lower()
    }

def make_computational_event(event_id, timestamp, classification, confidence, anomaly_score, text):
    raw_path, digest = write_raw(event_id, text)
    return {
        "event_id": event_id,
        "domain": "computational",
        "timestamp_utc": timestamp,
        "system": "Axiom/Gateway",
        "classification": classification,
        "tier": "T3",
        "confidence": confidence,
        "anomaly_score": anomaly_score,
        "raw_file": str(raw_path.relative_to(OUT_DIR)),
        "raw_hash_sha256": f"sha256:{digest}",
        "hash_method": "sha256_raw_file_v1",
        "independence_group": "axiom_gateway_computational",
        "contamination_risk": 0.20,
        "negative_null": "negative-null" in text.lower()
    }

def make_cognitive_event(event_id, timestamp, text, specificity, confidence, anomaly_score):
    raw_text = "\n".join([
        f"event_id={event_id}",
        f"timestamp_utc={timestamp}",
        f"text={text}",
        "locked_before_outcome=false",
        "study_id=AXIOM-XDOMAIN-001"
    ])
    raw_path, digest = write_raw(event_id, raw_text)
    return {
        "event_id": event_id,
        "domain": "cognitive",
        "timestamp_utc": timestamp,
        "report_type": "retrospective_seed_prediction",
        "text": text,
        "specificity": specificity,
        "confidence": confidence,
        "anomaly_score": anomaly_score,
        "locked_before_outcome": False,
        "raw_file": str(raw_path.relative_to(OUT_DIR)),
        "raw_hash_sha256": f"sha256:{digest}",
        "hash_method": "sha256_raw_file_v1",
        "hash_created_before_outcome": False,
        "independence_group": "user_cognitive_seed",
        "contamination_risk": 0.45,
        "negative_null": False
    }

def main():
    kb = load_json(KB_FILE)
    sources = load_json(SOURCES_FILE)
    changelog = load_json(CHANGELOG_FILE)

    physical_specs = [
        ("3i_spherex_observations_2026_02_04", 0.75),
        ("3i_isotopic_composition_2026_03_06", 0.90),
        ("3i_post_perihelion_spectroscopy_2026_02_27", 0.80),
        ("3i_nongrav_uncertainty_2026_02_28", 0.75),
        ("3i_jpl_horizons_solution_snapshot_2026_02_19", 0.65),
        ("3i_jupiter_approach_geometry_2026_03_16", 0.55),
        ("3i_breakthrough_listen_no_technosignature", 0.70),
        ("3i_tess_special_run_2026_jan", 0.55),
        ("3i_tess_tssc_hlsp_2026_01", 0.55),
        ("3i_open_nasa_data_archives_2026_03_20", 0.50)
    ]

    events = []

    for fact_id, anomaly_score in physical_specs:
        ev = make_physical_event(kb, fact_id, anomaly_score)
        if ev:
            events.append(ev)

    # Retrospective seed cognitive entries.
    # These are useful for structure/testing but do NOT prove pre-event prediction.
    events.extend([
        make_cognitive_event(
            "C_seed_isotopes_20260305",
            "2026-03-05T12:00:00Z",
            "Water or isotope anomaly update likely within 72 hours.",
            0.85, 0.70, 0.70
        ),
        make_cognitive_event(
            "C_seed_spectroscopy_20260226",
            "2026-02-26T12:00:00Z",
            "Spectroscopy may introduce new ambiguity or metal-emission detail.",
            0.80, 0.68, 0.65
        ),
        make_cognitive_event(
            "C_seed_nga_20260227",
            "2026-02-27T12:00:00Z",
            "NGA uncertainty or orbital-model sensitivity update likely.",
            0.80, 0.70, 0.68
        ),
        make_cognitive_event(
            "C_seed_jupiter_20260315",
            "2026-03-15T12:00:00Z",
            "Geometry or trajectory update likely within 48 hours.",
            0.75, 0.65, 0.60
        )
    ])

    events.extend([
        make_computational_event(
            "K_axiom_candidate_root_20260429",
            "2026-04-29T00:00:00Z",
            "T3_instrumented_pattern",
            0.92,
            0.70,
            "Axiom Guard v2.14.0-candidate registered as bounded governance sidecar; not AGI, not consciousness, not KB replacement."
        ),
        make_computational_event(
            "K_negative_null_behavior_20260429",
            "2026-04-29T00:01:00Z",
            "T3_governance_rule",
            0.90,
            0.65,
            "Axiom Guard classifies non-detection claims as bounded negative-null observations, not proof of absence."
        ),
        make_computational_event(
            "K_baam_framework_20251107",
            "2025-11-07T00:00:00Z",
            "T3_analysis_tool",
            0.85,
            0.60,
            "BAAM framework uses tier/confidence weighting and Bayesian anomaly comparison with guardrails."
        ),
        make_computational_event(
            "K_chi_audit_20251202",
            "2025-12-02T12:00:00Z",
            "T1_internal_audit",
            0.95,
            0.50,
            "CHI audit passed with CHI 9.7 and entropy leak 0.01."
        ),
        make_computational_event(
            "K_post_seal_refresh_20260314",
            "2026-03-14T00:00:00Z",
            "T3_instrumented_pattern",
            0.85,
            0.75,
            "v2.12.4 post-seal cumulative patch added SPHEREx, isotope, spectroscopy, NGA, JPL solution, and Jupiter geometry entries."
        )
    ])

    payload = {
        "study_id": "AXIOM-XDOMAIN-001",
        "version": "0.3-kb-derived",
        "created_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_files": [
            "knowledge_base_merged_v2.json",
            "sources.json",
            "kb_changelog.json",
            "kb_updates_cumulative.json"
        ],
        "notes": [
            "Physical events are derived from current KB facts.",
            "Cognitive seed entries are retrospective and hash_created_before_outcome=false.",
            "Computational entries are governance/runtime-derived seed entries.",
            "This dataset is suitable for pipeline testing and T3 screening, not T2 validation."
        ],
        "events": events
    }

    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    print(f"Created {OUT_FILE}")
    print(f"Events: {len(events)}")
    print(f"Raw files: {RAW_DIR}")
    print("Next:")
    print(f"  python3 scripts/axiom_correlate.py {OUT_FILE}")

if __name__ == "__main__":
    main()
