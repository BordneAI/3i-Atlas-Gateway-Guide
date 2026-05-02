#!/usr/bin/env python3
"""
Read-only KB source-tier / provenance policy audit.

This script reports AXIOM-aligned provenance-policy risks that are not
necessarily covered by structural KB validators.

It does not mutate files.
It does not ingest events.
It does not match predictions.
It does not score outcomes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "sources": ROOT / "sources.json",
    "kb": ROOT / "knowledge_base_merged_v2.json",
    "updates": ROOT / "kb_updates_cumulative.json",
    "tags": ROOT / "tags_index.json",
    "manifest": ROOT / "manifest.json",
}

HIGH_TIERS = {"T0", "T1", "T2"}

REVIEW_GATED_TERMS = (
    "under_review",
    "under review",
    "needs_verification",
    "needs verification",
    "verification_required",
    "verification required",
    "needs_direct",
    "needs direct",
    "pending verification",
    "review-gated",
    "review gated",
)

TIME_SENSITIVE_TERMS = (
    "current",
    "latest",
    "ephemeris",
    "visibility",
    "observing",
    "magnitude",
    "ra",
    "dec",
    "coordinates",
    "trajectory",
    "position",
    "campaign",
    "schedule",
    "window",
    "deadline",
    "perihelion",
    "post-perihelion",
    "nongravitational",
    "lightcurve",
)

METHODOLOGY_TERMS = (
    "analysis_tool",
    "analysis tool",
    "bayesian_framework",
    "bayesian framework",
    "baam",
    "axiom guard",
    "runtime audit",
    "audit artifact",
    "governance surface",
)

AAIV_TERMS = ("aaiv", "alien artificial intelligence validation")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_json(path: Path, findings: List[Dict[str, Any]]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        add_finding(
            findings,
            severity="fail",
            category="file_missing",
            file=str(path.relative_to(ROOT)),
            path=str(path.relative_to(ROOT)),
            message="Required KB audit file is missing.",
            recommended_action="Restore the file or remove it from the audit scope.",
        )
    except json.JSONDecodeError as exc:
        add_finding(
            findings,
            severity="fail",
            category="json_parse_error",
            file=str(path.relative_to(ROOT)),
            path=str(path.relative_to(ROOT)),
            message=f"JSON parse error: {exc}",
            recommended_action="Fix JSON syntax before running policy audit.",
        )
    return None


def tier_base(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    match = re.search(r"T[0-5]", value.upper())
    return match.group(0) if match else None


def lower_blob(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    except TypeError:
        return str(value).lower()


def is_preprint_like(entry: Dict[str, Any]) -> bool:
    blob = lower_blob(entry)
    typ = str(entry.get("type", "")).lower()
    notes = str(entry.get("notes", "")).lower()
    title = str(entry.get("title", "")).lower()

    explicit_preprint = (
        typ == "preprint"
        or "preprint" in title
        or "preprint" in notes
        or "peer-review pending" in blob
        or "peer review pending" in blob
        or "not yet peer-reviewed" in blob
        or "not yet peer reviewed" in blob
    )

    arxiv_only_signal = "arxiv.org" in blob or "arxiv" in typ or "arxiv" in title or "arxiv" in notes

    peer_review_positive = (
        ("peer-reviewed" in blob or "peer reviewed" in blob)
        and "not yet peer-reviewed" not in blob
        and "not yet peer reviewed" not in blob
        and "peer-review pending" not in blob
        and "peer review pending" not in blob
    )

    return (explicit_preprint or arxiv_only_signal) and not peer_review_positive


def internal_methodology_reason(source_id: str, entry: Dict[str, Any]) -> Optional[str]:
    """Return a reason if the source is an internal/methodology/governance surface.

    This intentionally avoids broad terms like "local" or "internal" in free text,
    because those can appear in legitimate astronomy contexts.
    """
    sid = source_id.upper()
    typ = str(entry.get("type", "")).lower().strip()
    blob = lower_blob(entry)

    urls = entry.get("urls", entry.get("url", []))
    if isinstance(urls, str):
        urls = [urls]
    url_blob = " ".join(str(u).lower() for u in urls)

    if sid.startswith(("BAYESIAN-FRAMEWORK", "AXIOM-GUARD", "PATCH-")):
        return "source_id indicates internal methodology/governance/release artifact"

    if typ in {"analysis_tool", "internal_audit", "runtime_audit", "governance", "methodology"}:
        return f"type={typ}"

    if any(str(u).lower().startswith("[local]") for u in urls):
        return "local file reference"

    if "baam" in blob or "axiom guard" in blob or "runtime audit" in blob:
        return "methodology/governance terminology"

    return None


def source_entries(sources: Any) -> Iterable[Tuple[str, Dict[str, Any], str]]:
    seen: Set[str] = set()

    def emit_from_mapping(mapping: Dict[str, Any], prefix: str) -> Iterable[Tuple[str, Dict[str, Any], str]]:
        for source_id, entry in mapping.items():
            if source_id in seen:
                continue
            if not isinstance(entry, dict):
                continue
            if not any(k in entry for k in ("tier", "provenance_tier", "truth_tier", "urls", "url", "type", "publisher", "notes", "title")):
                continue
            seen.add(str(source_id))
            yield str(source_id), entry, f"{prefix}/{source_id}"

    if isinstance(sources, dict):
        nested = sources.get("sources")
        if isinstance(nested, dict):
            yield from emit_from_mapping(nested, "sources.json/sources")

        # Current repo shape appears to use top-level source IDs.
        yield from emit_from_mapping(sources, "sources.json")


def walk(node: Any, path: str = "$") -> Iterable[Tuple[str, Any]]:
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            safe_key = str(key).replace("/", "~1")
            yield from walk(value, f"{path}/{safe_key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}/{index}")


def parse_date(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None

    text = value.strip()
    # Accept date-only or ISO-ish UTC forms.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text = text + "T00:00:00Z"

    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def add_finding(
    findings: List[Dict[str, Any]],
    *,
    severity: str,
    category: str,
    file: str,
    path: str,
    message: str,
    recommended_action: str,
    current_value: Any = None,
    source_id: Optional[str] = None,
    proposal_id: Optional[str] = None,
) -> None:
    finding: Dict[str, Any] = {
        "severity": severity,
        "category": category,
        "file": file,
        "path": path,
        "message": message,
        "recommended_action": recommended_action,
    }
    if current_value is not None:
        finding["current_value"] = current_value
    if source_id:
        finding["source_id"] = source_id
    if proposal_id:
        finding["proposal_id"] = proposal_id
    findings.append(finding)


def audit_sources(sources: Any, findings: List[Dict[str, Any]]) -> Tuple[Set[str], Set[str], Set[str]]:
    source_ids: Set[str] = set()
    review_source_ids: Set[str] = set()
    methodology_source_ids: Set[str] = set()

    for source_id, entry, path in source_entries(sources):
        source_ids.add(source_id)

        tier = tier_base(entry.get("tier") or entry.get("provenance_tier") or entry.get("truth_tier"))
        blob = lower_blob(entry)

        if is_preprint_like(entry) and tier in HIGH_TIERS:
            review_source_ids.add(source_id)
            add_finding(
                findings,
                severity="warn",
                category="preprint_over_tiered",
                file="sources.json",
                path=f"{path}/tier",
                source_id=source_id,
                current_value=entry.get("tier"),
                message="arXiv/preprint-like source is tiered above T3.",
                recommended_action="Review for demotion to T3 provisional unless independently validated by peer review, agency/archive release, MPC/JPL record, or equivalent primary confirmation.",
            )

        methodology_reason = internal_methodology_reason(source_id, entry)
        is_methodology = methodology_reason is not None
        if is_methodology:
            methodology_source_ids.add(source_id)

        if is_methodology and tier in HIGH_TIERS:
            review_source_ids.add(source_id)
            add_finding(
                findings,
                severity="warn",
                category="internal_tool_over_tiered",
                file="sources.json",
                path=f"{path}/tier",
                source_id=source_id,
                current_value=entry.get("tier"),
                message="Internal/local methodology or analysis surface is tiered as T1/T2 evidence.",
                recommended_action="Treat as methodology/governance surface, not T1/T2 scientific evidence.",
            )

        is_aaiv = any(term in blob for term in AAIV_TERMS)
        if is_aaiv and tier != "T4":
            review_source_ids.add(source_id)
            add_finding(
                findings,
                severity="warn",
                category="methodology_used_as_evidence",
                file="sources.json",
                path=f"{path}/tier",
                source_id=source_id,
                current_value=entry.get("tier"),
                message="AAIV-related source is not tiered as T4/hypothesis-generator.",
                recommended_action="Review AAIV boundary. AAIV should remain T4-only / hypothesis-generator unless separately validated.",
            )

        boundary_terms = ("baam", "axiom guard", "runtime audit")
        if any(term in blob for term in boundary_terms) and tier in HIGH_TIERS:
            review_source_ids.add(source_id)
            add_finding(
                findings,
                severity="warn",
                category="methodology_used_as_evidence",
                file="sources.json",
                path=f"{path}/tier",
                source_id=source_id,
                current_value=entry.get("tier"),
                message="BAAM / Axiom Guard / runtime audit surface is tiered as high evidence.",
                recommended_action="Keep as methodology/governance surface unless separately validated as external evidence.",
            )

    return source_ids, review_source_ids, methodology_source_ids


def extract_cited_source_ids(node: Any, known_source_ids: Set[str]) -> Set[str]:
    cited: Set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, str):
            if value in known_source_ids:
                cited.add(value)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)

    if isinstance(node, dict):
        for key, value in node.items():
            key_l = str(key).lower()
            if key_l in {
                "source",
                "sources",
                "source_id",
                "source_ids",
                "citation",
                "citations",
                "references",
                "reference_ids",
            } or "source" in key_l:
                collect(value)

    return cited


def audit_kb(
    kb: Any,
    findings: List[Dict[str, Any]],
    source_ids: Set[str],
    review_source_ids: Set[str],
    stale_days: int,
) -> None:
    if kb is None:
        return

    now = utc_now()
    seen_citations: Set[Tuple[str, str]] = set()

    for path, node in walk(kb, "knowledge_base_merged_v2.json"):
        if not isinstance(node, dict):
            continue

        cited = extract_cited_source_ids(node, source_ids)
        for source_id in sorted(cited & review_source_ids):
            key = (path, source_id)
            if key in seen_citations:
                continue
            seen_citations.add(key)
            add_finding(
                findings,
                severity="warn",
                category="kb_cites_review_source",
                file="knowledge_base_merged_v2.json",
                path=path,
                source_id=source_id,
                message="KB node cites a source ID flagged for tier/provenance manual review.",
                recommended_action="Review whether the KB claim should remain surfaced, be demoted, be caveated, or be routed to archival/manual review.",
            )

        effective_tier = tier_base(node.get("tier") or node.get("truth_tier") or node.get("provenance_tier"))
        if effective_tier in HIGH_TIERS:
            blob = lower_blob(node)
            if any(term in blob for term in TIME_SENSITIVE_TERMS):
                for date_key in ("as_of", "last_audit", "last_checked", "updated_at", "timestamp_utc"):
                    parsed = parse_date(node.get(date_key))
                    if not parsed:
                        continue
                    age_days = (now - parsed).days
                    if age_days > stale_days:
                        add_finding(
                            findings,
                            severity="warn",
                            category="stale_time_sensitive_claim",
                            file="knowledge_base_merged_v2.json",
                            path=f"{path}/{date_key}",
                            current_value=node.get(date_key),
                            message=f"Time-sensitive high-tier KB node has stale date metadata ({age_days} days old).",
                            recommended_action="Refresh from current T1/T2 source or route to archival with absolute date.",
                        )
                    break


def audit_updates(updates: Any, findings: List[Dict[str, Any]]) -> None:
    if updates is None:
        return

    seen: Set[str] = set()

    def check_record(path: str, node: Dict[str, Any]) -> None:
        proposal_id = node.get("proposal_id") or node.get("update_id") or node.get("id")
        key = str(proposal_id) if proposal_id else path
        if key in seen:
            return
        seen.add(key)

        blob = lower_blob(node)
        if any(term in blob for term in REVIEW_GATED_TERMS):
            add_finding(
                findings,
                severity="warn",
                category="integrated_but_under_review",
                file="kb_updates_cumulative.json",
                path=path,
                proposal_id=str(proposal_id) if proposal_id else None,
                message="Integrated/applied update record still contains review-gated or verification-required language.",
                recommended_action="Review whether this should remain integrated, be caveated, be marked archival, or be routed back to manual review.",
            )

    if isinstance(updates, dict):
        for key in ("integrated", "applied", "closed", "accepted"):
            value = updates.get(key)
            if isinstance(value, list):
                for index, record in enumerate(value):
                    if isinstance(record, dict):
                        check_record(f"kb_updates_cumulative.json/{key}/{index}", record)

    # Fallback for alternate shapes: only check nodes that carry their own ID.
    for path, node in walk(updates, "kb_updates_cumulative.json"):
        if not isinstance(node, dict):
            continue
        proposal_id = node.get("proposal_id") or node.get("update_id") or node.get("id")
        if not proposal_id:
            continue
        appears_integrated = (
            str(node.get("status", "")).lower() in {"integrated", "applied", "closed"}
            or str(node.get("decision", "")).lower() in {"integrated", "accepted", "applied"}
        )
        if appears_integrated:
            check_record(path, node)


def audit_tags(tags: Any, findings: List[Dict[str, Any]]) -> None:
    if tags is None:
        return

    blob = lower_blob(tags)
    risky_tags = [
        "testable_prediction",
        "truth_tier",
        "false_tier",
        "grok_analysis",
        "unverified",
    ]
    present = [tag for tag in risky_tags if tag in blob]
    if present:
        add_finding(
            findings,
            severity="info",
            category="tag_metadata_evidence_risk",
            file="tags_index.json",
            path="tags_index.json",
            current_value=present,
            message="Tags with evidence-like names are present.",
            recommended_action="Keep tags as routing/discovery metadata only. Do not treat tags as source validation, event scoring, or factual promotion.",
        )


def audit_manifest(manifest: Any, findings: List[Dict[str, Any]]) -> None:
    if manifest is None:
        return

    blob = lower_blob(manifest)

    if "preprint" in blob and re.search(r"\bT2\b|\"t2\"|t2 ", blob, flags=re.IGNORECASE):
        add_finding(
            findings,
            severity="warn",
            category="tier_policy_mismatch",
            file="manifest.json",
            path="manifest.json",
            message="Manifest appears to contain T2/preprint tier wording that may conflict with stricter AXIOM audit rules.",
            recommended_action="Clarify that arXiv-only / peer-review-pending preprints default to T3 provisional unless separately validated.",
        )

    if "axiom-xdomain" in blob or "xdomain" in blob:
        add_finding(
            findings,
            severity="info",
            category="experiment_output_kb_contamination_risk",
            file="manifest.json",
            path="manifest.json",
            message="Manifest references AXIOM/XDOMAIN-related governance or experiment surfaces.",
            recommended_action="Ensure AXIOM-XDOMAIN outputs remain experimental/T3 unless separately reviewed and promoted.",
        )


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    loaded = {name: load_json(path, findings) for name, path in FILES.items()}

    source_ids, review_source_ids, _methodology_ids = audit_sources(loaded.get("sources"), findings)
    audit_kb(loaded.get("kb"), findings, source_ids, review_source_ids, args.stale_days)
    audit_updates(loaded.get("updates"), findings)
    audit_tags(loaded.get("tags"), findings)
    audit_manifest(loaded.get("manifest"), findings)

    counts = defaultdict(int)
    by_category = defaultdict(int)
    by_file = defaultdict(int)

    for finding in findings:
        counts[finding["severity"]] += 1
        by_category[finding["category"]] += 1
        by_file[finding["file"]] += 1

    status = "pass"
    if counts["fail"]:
        status = "fail"
    elif counts["warn"]:
        status = "warn"

    return {
        "audit": "kb_source_tier_audit",
        "generated_utc": utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": "read_only",
        "status": status,
        "summary": {
            "n_findings": len(findings),
            "n_fail": counts["fail"],
            "n_warn": counts["warn"],
            "n_info": counts["info"],
            "by_category": dict(sorted(by_category.items())),
            "by_file": dict(sorted(by_file.items())),
        },
        "files_checked": {name: str(path.relative_to(ROOT)) for name, path in FILES.items()},
        "policy": {
            "preprint_default": "T3 provisional unless separately validated",
            "internal_methodology": "methodology/governance surface, not T1/T2 evidence",
            "aaiv": "T4-only / hypothesis-generator unless separately validated",
            "tags": "metadata only, not evidence",
            "xdomain": "experimental/T3 unless separately reviewed and promoted",
        },
        "findings": findings,
    }


def print_human(report: Dict[str, Any]) -> None:
    print("KB Source-Tier Policy Audit")
    print("===========================")
    print(f"Generated UTC: {report['generated_utc']}")
    print(f"Mode: {report['mode']}")
    print(f"Status: {report['status'].upper()}")
    print()

    summary = report["summary"]
    print(
        f"Findings: {summary['n_findings']} "
        f"(fail={summary['n_fail']}, warn={summary['n_warn']}, info={summary['n_info']})"
    )
    print()

    if summary["by_category"]:
        print("Findings by category:")
        for category, count in summary["by_category"].items():
            print(f"- {category}: {count}")
        print()

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for finding in report["findings"]:
        grouped[finding["file"]].append(finding)

    if not grouped:
        print("No findings.")
        return

    for file_name, findings in sorted(grouped.items()):
        print(f"## {file_name}")
        for idx, finding in enumerate(findings, start=1):
            print(f"{idx}. [{finding['severity'].upper()}] {finding['category']}")
            if finding.get("source_id"):
                print(f"   source_id: {finding['source_id']}")
            if finding.get("proposal_id"):
                print(f"   proposal_id: {finding['proposal_id']}")
            print(f"   path: {finding['path']}")
            if "current_value" in finding:
                print(f"   current_value: {finding['current_value']}")
            print(f"   message: {finding['message']}")
            print(f"   recommended_action: {finding['recommended_action']}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only KB source-tier / provenance policy audit."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument(
        "--stale-days",
        type=int,
        default=30,
        help="Age threshold for stale time-sensitive T1/T2 operational claims.",
    )
    args = parser.parse_args()

    report = build_report(args)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)

    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
