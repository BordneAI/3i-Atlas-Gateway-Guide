#!/usr/bin/env python3
"""Axiom Guard release preflight for v2.14.0-candidate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "2.14.0-candidate"
PACKAGE_ALIGNED_JSON = {
    "knowledge_base_merged_v2.json": ("version", "kb_version"),
    "kb_updates_cumulative.json": ("version", "updates_version"),
    "kb_changelog.json": ("version", "changelog_version"),
    "sources.json": ("version", "sources_version"),
    "tags_index.json": ("version",),
    "conversation_starters.json": ("version",),
    "stress_test_framework.json": ("version",),
}
REQUIRED_GUARD_FILES = (
    "README.md",
    "INTEGRATION.md",
    "pyproject.toml",
    "run_demo.py",
    "run_axiom_guard.sh",
    "smoke_commands.txt",
    "AxiomAdvancedSpec.lean",
    "verification_summary.json",
    "axiom_ai",
    "tests",
)
CITATION_KEYS = {"source_id", "source_ids", "sources", "citations"}
QUARANTINE_KEYS = {"quarantine", "_quarantine", "_quarantined", "quarantined_nodes"}
HIGH_TIERS = {"T1", "T2"}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Axiom Guard release preflight checks")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plain", action="store_true", help="print human-readable output")
    mode.add_argument("--json", action="store_true", help="print machine-readable output")
    return parser.parse_args(argv)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def tier_base(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"^(T[0-5]|F[0-7])", value)
    return match.group(1) if match else None


def source_ids_from(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


class Preflight:
    def __init__(self) -> None:
        self.checks: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}

    def pass_check(self, name: str, details: str | Mapping[str, Any] = "") -> None:
        self.checks.append({"name": name, "status": "pass", "details": details})

    def fail_check(self, name: str, code: str, message: str, location: str = "") -> None:
        error = {"check": name, "code": code, "message": message, "location": location}
        self.errors.append(error)
        self.checks.append({"name": name, "status": "fail", "details": error})

    def run(self) -> Dict[str, Any]:
        manifest = self.check_manifest()
        self.check_axiom_guard_tree()
        self.check_axiom_guard_tests()
        self.check_negative_null_smoke()
        if manifest:
            self.check_package_aligned_json(manifest)
        self.check_duplicate_proposals()
        self.check_changelog_entry()
        self.check_source_promotion()
        self.check_public_facts()
        self.check_kb_validator()
        return {
            "status": "fail" if self.errors else "pass",
            "expected_version": EXPECTED_VERSION,
            "checks": self.checks,
            "errors": self.errors,
        }

    def check_manifest(self) -> Mapping[str, Any] | None:
        name = "manifest_version"
        path = ROOT / "manifest.json"
        if not path.exists():
            self.fail_check(name, "manifest_missing", "manifest.json does not exist.", "manifest.json")
            return None
        try:
            manifest = load_json(path)
        except (OSError, json.JSONDecodeError) as error:
            self.fail_check(name, "manifest_unreadable", str(error), "manifest.json")
            return None

        expected_fields = {
            "version": EXPECTED_VERSION,
            "release_date": "2026-04-29",
            "release_state": "candidate",
            "release_type": "minor_candidate",
        }
        mismatches = {
            key: {"actual": manifest.get(key), "expected": value}
            for key, value in expected_fields.items()
            if manifest.get(key) != value
        }
        if mismatches:
            self.fail_check(name, "manifest_release_field_mismatch", json.dumps(mismatches, sort_keys=True), "manifest.json")
            return manifest
        self.pass_check(name, expected_fields)
        return manifest

    def check_axiom_guard_tree(self) -> None:
        name = "axiom_guard_tree"
        root = ROOT / "tools" / "axiom_guard"
        if not root.is_dir():
            self.fail_check(name, "axiom_guard_missing", "tools/axiom_guard does not exist.", "tools/axiom_guard")
            return
        missing = [entry for entry in REQUIRED_GUARD_FILES if not (root / entry).exists()]
        if missing:
            self.fail_check(name, "axiom_guard_files_missing", ", ".join(missing), "tools/axiom_guard")
            return
        self.pass_check(name, {"required_files": list(REQUIRED_GUARD_FILES)})

    def check_axiom_guard_tests(self) -> None:
        name = "axiom_guard_unit_tests"
        result = self._run([sys.executable, "-S", "-m", "unittest", "discover", "-s", "tools/axiom_guard/tests", "-v"])
        if result.returncode != 0:
            self.fail_check(name, "axiom_guard_tests_failed", self._short_output(result), "tools/axiom_guard/tests")
            return
        self.pass_check(name, "unit tests passed")

    def check_negative_null_smoke(self) -> None:
        name = "negative_null_smoke"
        result = self._run(["tools/axiom_guard/run_axiom_guard.sh", "--json", "--no-persist"])
        if result.returncode != 0:
            self.fail_check(name, "axiom_guard_smoke_failed", self._short_output(result), "tools/axiom_guard/run_axiom_guard.sh")
            return
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail_check(name, "axiom_guard_smoke_json_invalid", str(error), "tools/axiom_guard/run_axiom_guard.sh")
            return
        guard = payload.get("result", {})
        if guard.get("classification") != "Negative Null" or guard.get("detection_status") != "bounded non-detection":
            self.fail_check(name, "axiom_guard_smoke_semantics_failed", json.dumps(guard, sort_keys=True), "tools/axiom_guard/run_axiom_guard.sh")
            return
        self.pass_check(name, {"classification": guard.get("classification"), "detection_status": guard.get("detection_status")})

    def check_package_aligned_json(self, manifest: Mapping[str, Any]) -> None:
        name = "package_aligned_json"
        errors: List[str] = []
        files = manifest.get("files", {})
        for file_name, fields in PACKAGE_ALIGNED_JSON.items():
            path = ROOT / file_name
            if not path.exists():
                errors.append(f"{file_name}: missing")
                continue
            try:
                data = load_json(path)
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"{file_name}: {error}")
                continue
            manifest_entry = files.get(file_name, {}) if isinstance(files, Mapping) else {}
            if isinstance(manifest_entry, Mapping) and manifest_entry.get("version") not in (None, EXPECTED_VERSION):
                errors.append(f"manifest.files.{file_name}.version={manifest_entry.get('version')}")
            for field in fields:
                if data.get(field) != EXPECTED_VERSION:
                    errors.append(f"{file_name}.{field}={data.get(field)}")
        if errors:
            self.fail_check(name, "package_json_version_mismatch", "; ".join(errors), "manifest.json")
            return
        self.pass_check(name, {"version": EXPECTED_VERSION, "files": sorted(PACKAGE_ALIGNED_JSON)})

    def check_duplicate_proposals(self) -> None:
        name = "kb_updates_duplicate_proposal_ids"
        try:
            updates = load_json(ROOT / "kb_updates_cumulative.json")
        except (OSError, json.JSONDecodeError) as error:
            self.fail_check(name, "kb_updates_unreadable", str(error), "kb_updates_cumulative.json")
            return
        seen: Dict[str, str] = {}
        duplicates: List[str] = []
        for bucket in ("pending", "integrated", "rejected"):
            rows = updates.get(bucket, [])
            if not isinstance(rows, list):
                self.fail_check(name, "kb_updates_bucket_invalid", f"{bucket} must be an array.", f"kb_updates_cumulative.{bucket}")
                return
            for index, row in enumerate(rows):
                if not isinstance(row, Mapping):
                    continue
                proposal_id = row.get("proposal_id")
                if not isinstance(proposal_id, str) or not proposal_id:
                    continue
                location = f"kb_updates_cumulative.{bucket}[{index}].proposal_id"
                if proposal_id in seen:
                    duplicates.append(f"{proposal_id}: {seen[proposal_id]}, {location}")
                else:
                    seen[proposal_id] = location
        if duplicates:
            self.fail_check(name, "duplicate_proposal_id", "; ".join(duplicates), "kb_updates_cumulative.json")
            return
        self.pass_check(name, {"proposal_ids_checked": len(seen)})

    def check_changelog_entry(self) -> None:
        name = "kb_changelog_axiom_entry"
        try:
            changelog = load_json(ROOT / "kb_changelog.json")
        except (OSError, json.JSONDecodeError) as error:
            self.fail_check(name, "kb_changelog_unreadable", str(error), "kb_changelog.json")
            return
        haystack = json.dumps(changelog, sort_keys=True).lower()
        if "axiom guard" not in haystack or EXPECTED_VERSION not in haystack:
            self.fail_check(name, "axiom_changelog_entry_missing", "kb_changelog lacks an Axiom Guard integration entry for v2.14.0-candidate.", "kb_changelog.json")
            return
        self.pass_check(name, "Axiom Guard integration entry present")

    def check_source_promotion(self) -> None:
        name = "no_t4_or_quarantine_promotion"
        try:
            sources = load_json(ROOT / "sources.json")
            kb = load_json(ROOT / "knowledge_base_merged_v2.json")
        except (OSError, json.JSONDecodeError) as error:
            self.fail_check(name, "source_or_kb_unreadable", str(error), "knowledge_base_merged_v2.json")
            return
        source_tiers, quarantined = self._source_registry(sources)
        violations: List[str] = []

        def walk(node: Any, location: str, hidden: bool) -> None:
            if isinstance(node, list):
                for index, item in enumerate(node):
                    walk(item, f"{location}[{index}]", hidden)
                return
            if not isinstance(node, Mapping):
                return

            local_hidden = hidden or node.get("do_not_surface") is True
            effective_tier = tier_base(node.get("truth_tier")) or tier_base(node.get("tier")) or tier_base(node.get("provenance_tier"))
            cited = self._node_citations(node)
            if not local_hidden and effective_tier in HIGH_TIERS:
                for source_id in cited:
                    source_tier = source_tiers.get(source_id)
                    if source_id in quarantined:
                        violations.append(f"{location}: {effective_tier} cites quarantined {source_id}")
                    if source_tier == "T4":
                        violations.append(f"{location}: {effective_tier} cites T4 source {source_id}")
            for key, value in node.items():
                walk(value, f"{location}.{key}" if location else key, local_hidden or key in QUARANTINE_KEYS)

        walk(kb, "knowledge_base_merged_v2", False)
        if violations:
            self.fail_check(name, "promoted_low_tier_source", "; ".join(violations[:20]), "knowledge_base_merged_v2.json")
            return
        self.pass_check(name, "no surfaced T1/T2 node cites T4 or quarantined sources")

    def check_public_facts(self) -> None:
        name = "public_fact_metadata"
        try:
            kb = load_json(ROOT / "knowledge_base_merged_v2.json")
        except (OSError, json.JSONDecodeError) as error:
            self.fail_check(name, "kb_unreadable", str(error), "knowledge_base_merged_v2.json")
            return
        facts = kb.get("facts")
        if not isinstance(facts, list):
            self.fail_check(name, "facts_array_missing", "knowledge_base_merged_v2.facts must be an array.", "knowledge_base_merged_v2.facts")
            return
        errors: List[str] = []
        for index, fact in enumerate(facts):
            if not isinstance(fact, Mapping):
                continue
            location = f"knowledge_base_merged_v2.facts[{index}]"
            if not any(fact.get(key) for key in ("tier", "truth_tier", "provenance_tier")):
                errors.append(f"{location}: missing tier")
            if not fact.get("confidence"):
                errors.append(f"{location}: missing confidence")
            if not fact.get("as_of"):
                errors.append(f"{location}: missing as_of")
            if not self._node_citations(fact):
                errors.append(f"{location}: missing sources")
        if errors:
            self.fail_check(name, "public_fact_metadata_missing", "; ".join(errors[:30]), "knowledge_base_merged_v2.facts")
            return
        self.pass_check(name, {"facts_checked": len(facts)})

    def check_kb_validator(self) -> None:
        name = "validate_kb_json"
        result = self._run(["node", "scripts/validate_kb.js", "--json"])
        if result.returncode != 0:
            self.fail_check(name, "validate_kb_failed", self._short_output(result), "scripts/validate_kb.js")
            return
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail_check(name, "validate_kb_json_invalid", str(error), "scripts/validate_kb.js")
            return
        if payload.get("status") != "pass":
            self.fail_check(name, "validate_kb_status_failed", json.dumps(payload.get("errors", []), sort_keys=True), "scripts/validate_kb.js")
            return
        self.pass_check(name, payload.get("counts", {}))

    def _run(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED", "1")
        return subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, env=env)

    @staticmethod
    def _short_output(result: subprocess.CompletedProcess[str]) -> str:
        combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        return combined[-4000:] if combined else f"exit code {result.returncode}"

    @staticmethod
    def _node_citations(node: Mapping[str, Any]) -> List[str]:
        out: List[str] = []
        for key in CITATION_KEYS:
            out.extend(source_ids_from(node.get(key)))
        return out

    @staticmethod
    def _source_registry(sources: Mapping[str, Any]) -> tuple[Dict[str, str], set[str]]:
        tiers: Dict[str, str] = {}
        quarantined: set[str] = set()
        for key, value in sources.items():
            if key in {"_quarantined", "_quarantined_meta"}:
                continue
            if isinstance(value, Mapping):
                tier = tier_base(value.get("tier")) or tier_base(value.get("provenance_tier"))
                if tier:
                    tiers[key] = tier
        q = sources.get("_quarantined")
        if isinstance(q, list):
            quarantined.update(item for item in q if isinstance(item, str))
        elif isinstance(q, Mapping):
            quarantined.update(key for key in q.keys() if isinstance(key, str))
            for key, value in q.items():
                if isinstance(value, Mapping):
                    tier = tier_base(value.get("tier")) or tier_base(value.get("provenance_tier"))
                    if tier:
                        tiers[key] = tier
        return tiers, quarantined


def render_plain(report: Mapping[str, Any]) -> str:
    lines = [f"Axiom preflight: {str(report['status']).upper()}"]
    for check in report["checks"]:
        marker = "PASS" if check["status"] == "pass" else "FAIL"
        lines.append(f"[{marker}] {check['name']}")
        if check["status"] == "fail":
            details = check.get("details", {})
            if isinstance(details, Mapping):
                lines.append(f"  {details.get('code')}: {details.get('message')}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = Preflight().run()
    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_plain(report) + "\n")
    return 1 if report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
