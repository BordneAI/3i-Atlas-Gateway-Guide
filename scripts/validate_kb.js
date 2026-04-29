#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { computeFingerprint, JSON_SURFACES, TEXT_SURFACES } = require("./lib/release_signatures");
const { verifyGitReleaseSignature } = require("./lib/git_signature_verifier");

const ROOT = process.cwd();
const JSON_FILES = [
  "manifest.json",
  "knowledge_base_merged_v2.json",
  "kb_updates_cumulative.json",
  "kb_changelog.json",
  "sources.json",
  "tags_index.json",
  "conversation_starters.json",
  "stress_test_framework.json",
  "bayesian_framework.json"
];
const TEXT_FILES = [
  "instructions.txt"
];
const PACKAGE_ALIGNED_JSON = new Set([
  "knowledge_base_merged_v2.json",
  "kb_updates_cumulative.json",
  "kb_changelog.json",
  "sources.json",
  "tags_index.json",
  "conversation_starters.json",
  "stress_test_framework.json"
]);
const SIGNED_JSON = new Set(Object.keys(JSON_SURFACES).filter((file) => JSON_FILES.includes(file)));
const TIERS = new Set(["T0", "T1", "T2", "T3", "T4", "T5", "F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]);
const PROV = /^(T[0-5]|F[0-7])(?:_[A-Za-z0-9-]+)?$/;
const CITE = new Set(["source_id", "source_ids", "sources", "citations"]);
const QUAR = new Set(["quarantine", "_quarantine", "_quarantined", "quarantined_nodes"]);
const FLAGS = new Set(["--json", "--help", "--verify-git-signature", "--allow-dirty-git-signature"]);
const SEMVER = "(\\d+\\.\\d+\\.\\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?)";

function usage(code = 0) {
  (code ? process.stderr : process.stdout).write("Usage: node scripts/validate_kb.js [--json] [--verify-git-signature] [--allow-dirty-git-signature]\n");
  process.exit(code);
}
function args(argv) {
  const flags = argv.slice(2);
  for (const flag of flags) if (!FLAGS.has(flag)) usage(1);
  if (flags.includes("--help")) usage(0);
  return {
    json: flags.includes("--json"),
    verifyGitSignature: flags.includes("--verify-git-signature"),
    allowDirtyGitSignature: flags.includes("--allow-dirty-git-signature")
  };
}
function push(report, level, code, location, message) { report[level].push({ code, location, message }); }
function readText(file, report) {
  const full = path.join(ROOT, file);
  try { return fs.readFileSync(full, "utf8"); } catch (error) { push(report, "errors", "file_read_failed", file, error.message); return null; }
}
function readJson(file, report) {
  const raw = readText(file, report);
  if (raw == null) return null;
  try { return { data: JSON.parse(raw), raw }; } catch (error) { push(report, "errors", "json_parse_failed", file, error.message); return { data: null, raw }; }
}
function candidateId(id) { return typeof id === "string" && !id.startsWith("_") && /^[A-Z0-9][A-Z0-9_-]{5,79}$/.test(id) && (id.includes("-") || id.includes("_")); }
function nonEmpty(value) { return typeof value === "string" && value.trim().length > 0; }
function extractSemver(value) {
  if (typeof value !== "string") return null;
  const match = value.match(new RegExp(SEMVER));
  return match ? match[1] : null;
}
function isSourceRecord(key, value) {
  if (!candidateId(key) || !value || typeof value !== "object" || Array.isArray(value)) return false;
  const ok = nonEmpty(value.tier) && nonEmpty(value.title) && (nonEmpty(value.type) || nonEmpty(value.publisher));
  const urls = Array.isArray(value.urls) && value.urls.length > 0 && value.urls.every(nonEmpty);
  return ok && (urls || nonEmpty(value.path));
}
function scanTiers(node, loc, report) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) return node.forEach((item, i) => scanTiers(item, `${loc}[${i}]`, report));
  for (const [key, value] of Object.entries(node)) {
    const next = loc ? `${loc}.${key}` : key;
    const isStressSeverityTier = next.startsWith("stress_test_framework.tests[") && key === "tier";
    if (key === "tier" && !isStressSeverityTier && !TIERS.has(value)) push(report, "errors", "invalid_tier", next, `Invalid tier ${value}.`);
    if (key === "provenance_tier" && (typeof value !== "string" || !PROV.test(value))) push(report, "errors", "invalid_provenance_tier", next, `Invalid provenance_tier ${value}.`);
    scanTiers(value, next, report);
  }
}
function dirtyFiles(paths, report) {
  const result = spawnSync("git", ["status", "--porcelain", "--", ...paths], { cwd: ROOT, encoding: "utf8" });
  if (result.error || result.status !== 0) {
    push(report, "warnings", "git_status_unavailable", "git status --porcelain", "Could not inspect git dirtiness for tracked surfaces.");
    return new Set();
  }
  const dirty = new Set();
  result.stdout.split(/\r?\n/).filter(Boolean).forEach((line) => dirty.add(line.slice(3).trim().replace(/\\/g, "/")));
  return dirty;
}
function tokens(value) { return typeof value === "string" ? [...value.matchAll(new RegExp(`(?:^|[^0-9])${SEMVER}(?![0-9A-Za-z.-])`, "g"))].map((m) => m[1]) : []; }
function validateSignatures(file, data, dirty, report) {
  if (!data || typeof data.version !== "string") return;
  ["signature", "signature_footer", "validated_by", "validation_basis"].forEach((field) => tokens(data[field]).forEach((token) => {
    if (token !== data.version) push(report, data.signature_status === "signature_validated" ? "errors" : "warnings", "signature_version_drift", `${file}.${field}`, `${field} references ${token}, but ${file}.version is ${data.version}.`);
  }));
  if (SIGNED_JSON.has(file) && Object.prototype.hasOwnProperty.call(data, "fingerprint_sha256")) {
    const computed = computeFingerprint(data);
    if (computed !== data.fingerprint_sha256) {
      push(report, "errors", "fingerprint_mismatch", file, `Stored fingerprint does not match current content (${data.fingerprint_sha256} != ${computed}).`);
      if (data.signature_status === "signature_validated" && dirty.has(file)) push(report, "errors", "validated_surface_dirty", file, "File is dirty in git and its signed fingerprint is stale; run the local signature refresh command.");
    }
  }
}
function validateTextSurfaces(report) {
  TEXT_FILES.forEach((file) => {
    report.files_checked.push(file);
    const raw = readText(file, report);
    if (raw == null) return;
    const config = TEXT_SURFACES[file];
    if (!config) {
      push(report, "warnings", "text_surface_unconfigured", file, "No text surface validation config is registered for this file.");
      return;
    }
    const versionMatch = raw.match(config.versionRegex);
    if (!versionMatch) {
      push(report, "errors", "text_surface_version_missing", file, "Text surface is missing a recognizable version marker.");
      return;
    }
    const version = versionMatch[1];
    const signatureVersion = extractSignatureTokenVersion(raw);
    if (!/^Signature:\s*#ATLAS-SIG-/m.test(raw)) push(report, "errors", "text_surface_signature_missing", file, "Text surface is missing a Signature marker.");
    if (!/^signature_status:\s*"signature_validated"$/m.test(raw)) push(report, "errors", "text_surface_signature_status_missing", file, "Text surface is missing a validated signature_status marker.");
    if (!/^validated_by:\s*".+"$/m.test(raw)) push(report, "errors", "text_surface_validated_by_missing", file, "Text surface is missing a validated_by marker.");
    if (!/^signature_validated_at:\s*".+"$/m.test(raw)) push(report, "errors", "text_surface_signature_timestamp_missing", file, "Text surface is missing a signature_validated_at marker.");
    if (signatureVersion && signatureVersion !== version) push(report, "errors", "text_surface_signature_version_drift", file, `Signature token ${signatureVersion} does not match text surface version ${version}.`);
  });
}
function validateVersions(loaded, report) {
  const manifest = loaded["manifest.json"];
  if (!manifest) return;
  const mv = manifest.version;
  const packageFields = [
    ["knowledge_base_merged_v2.json", "kb_version"],
    ["kb_updates_cumulative.json", "updates_version"],
    ["kb_changelog.json", "changelog_version"],
    ["sources.json", "sources_version"]
  ];
  for (const file of JSON_FILES) {
    if (file === "manifest.json" || !loaded[file]) continue;
    const entry = manifest.files && manifest.files[file];
    if (entry && entry.version && loaded[file].version && entry.version !== loaded[file].version) {
      push(report, "errors", "manifest_file_version_mismatch", `manifest.files.${file}.version`, `manifest.files.${file}.version does not match ${file}.version.`);
    }
    if (PACKAGE_ALIGNED_JSON.has(file) && loaded[file].version !== mv) {
      push(report, "errors", "release_version_mismatch", `${file}.version`, `${file}.version must match manifest.version (${mv}).`);
    }
  }
  packageFields.forEach(([file, field]) => {
    if (loaded[file] && Object.prototype.hasOwnProperty.call(loaded[file], field) && loaded[file][field] !== mv) {
      push(report, "errors", "release_version_mismatch", `${file}.${field}`, `${file}.${field} must match manifest.version (${mv}).`);
    }
  });
}
function registry(sources, report) {
  const top = new Set(); const quar = new Set(); const seen = new Map();
  const note = (id, loc) => { if (!seen.has(id)) seen.set(id, []); seen.get(id).push(loc); };
  Object.keys(sources || {}).forEach((key) => {
    if (key === "_quarantined" || key === "_quarantined_meta") return;
    const value = sources[key];
    if (isSourceRecord(key, value)) { top.add(key); note(key, `sources.${key}`); }
    else if (candidateId(key) && value && typeof value === "object" && !Array.isArray(value)) push(report, "warnings", "source_record_missing_required_fields", `sources.${key}`, "Top-level source-like record is missing required fields.");
  });
  const q = sources ? sources._quarantined : undefined;
  if (Array.isArray(q)) q.forEach((value, i) => {
    if (typeof value === "string" && candidateId(value) && top.has(value)) { quar.add(value); note(value, `_quarantined[${i}]`); }
    else push(report, "warnings", "quarantine_container_schema_violation", `_quarantined[${i}]`, "Unexpected quarantine array entry.");
  });
  else if (q && typeof q === "object") Object.entries(q).forEach(([key, value]) => {
    if (isSourceRecord(key, value)) { quar.add(key); note(key, `_quarantined.${key}`); }
    else push(report, "warnings", "quarantine_container_schema_violation", `_quarantined.${key}`, "Unexpected quarantine object entry.");
  });
  else if (q !== undefined) push(report, "warnings", "quarantine_container_schema_violation", "_quarantined", "Unexpected quarantine container type.");
  for (const [id, locs] of seen.entries()) if (locs.length > 1) push(report, "errors", "duplicate_source_ids_detected", locs.join(", "), `Source ID ${id} appears in multiple registry/quarantine locations.`);
  return { top, quar };
}
function scanCitations(kb, quar, report) {
  const cited = new Set(); const surfaced = new Set();
  const walk = (node, loc, hidden, qctx) => {
    if (Array.isArray(node)) return node.forEach((item, i) => walk(item, `${loc}[${i}]`, hidden, qctx));
    if (!node || typeof node !== "object") return;
    const nowHidden = hidden || node.do_not_surface === true;
    for (const [key, value] of Object.entries(node)) {
      const next = loc ? `${loc}.${key}` : key;
      const nowQuar = qctx || QUAR.has(key);
      if (CITE.has(key)) {
        if (key === "source_id") {
          if (typeof value !== "string") push(report, "warnings", "citation_field_wrong_type", next, "source_id must be a string.");
          else if (candidateId(value)) { cited.add(value); if (!nowHidden && !nowQuar && quar.has(value)) surfaced.add(value); }
          else push(report, "warnings", "free_text_in_citation_fields", next, `Non-ID citation token ${value}.`);
        } else if (Array.isArray(value)) {
          value.forEach((entry, i) => {
            const itemLoc = `${next}[${i}]`;
            if (typeof entry !== "string") return push(report, "warnings", "non_string_in_citation_array", itemLoc, "Citation arrays must contain only strings.");
            if (candidateId(entry)) { cited.add(entry); if (!nowHidden && !nowQuar && quar.has(entry)) surfaced.add(entry); }
            else push(report, "warnings", "free_text_in_citation_fields", itemLoc, `Non-ID citation token ${entry}.`);
          });
        } else push(report, "warnings", "citation_field_wrong_type", next, "Citation field must be a string or array.");
      }
      walk(value, next, nowHidden, nowQuar);
    }
  };
  walk(kb, "knowledge_base_merged_v2", false, false);
  return { cited, surfaced: [...surfaced].sort() };
}
function countActions(rows) {
  const out = { adds_live: 0, updates_live: 0, carries_live: 0, holds_deferred: 0, demotions_stale: 0 };
  rows.forEach((row) => {
    const action = row && typeof row.action === "string" ? row.action.trim().toLowerCase() : "";
    if (action === "add") out.adds_live += 1;
    if (action === "update") out.updates_live += 1;
    if (action === "carry") out.carries_live += 1;
    if (action === "hold") out.holds_deferred += 1;
    if (action === "demote" || action === "flag") out.demotions_stale += 1;
  });
  return out;
}
function scanSummary(node, loc, report) {
  if (Array.isArray(node)) return node.forEach((item, i) => scanSummary(item, `${loc}[${i}]`, report));
  if (!node || typeof node !== "object") return;
  const keys = ["adds_live", "updates_live", "carries_live", "holds_deferred", "demotions_stale"];
  const rows = Array.isArray(node.integrated_entries) ? node.integrated_entries : Array.isArray(node.entries) && node.entries.some((entry) => entry && typeof entry.action === "string") ? node.entries : null;
  if (rows && keys.some((key) => typeof node[key] === "number")) {
    const actual = countActions(rows);
    keys.forEach((key) => {
      if (typeof node[key] === "number" && node[key] !== actual[key]) push(report, "errors", "summary_count_mismatch", `${loc}.${key}`, `${key} reports ${node[key]}, but explicit action rows total ${actual[key]}.`);
    });
  }
  Object.entries(node).forEach(([key, value]) => scanSummary(value, loc ? `${loc}.${key}` : key, report));
}
function dupIds(list, loc, keys, report) {
  const seen = new Map();
  list.forEach((item, i) => keys.forEach((key) => {
    const value = item && item[key];
    if (!nonEmpty(value)) return;
    const id = `${key}:${value}`;
    if (!seen.has(id)) seen.set(id, []);
    seen.get(id).push(`${loc}[${i}].${key}`);
  }));
  for (const [id, locs] of seen.entries()) if (locs.length > 1) push(report, "errors", "duplicate_ledger_id", locs.join(", "), `Duplicate ledger identifier ${id}.`);
}
function validateLedgers(loaded, report) {
  const updates = loaded["kb_updates_cumulative.json"], changelog = loaded["kb_changelog.json"];
  if (updates) {
    ["pending", "integrated", "rejected"].forEach((bucket) => { if (!Array.isArray(updates[bucket])) push(report, "errors", "unsupported_schema", `kb_updates_cumulative.${bucket}`, `${bucket} must be an array.`); });
    if (Array.isArray(updates.pending)) dupIds(updates.pending, "kb_updates_cumulative.pending", ["proposal_id"], report);
    if (Array.isArray(updates.integrated)) dupIds(updates.integrated, "kb_updates_cumulative.integrated", ["proposal_id"], report);
    if (Array.isArray(updates.rejected)) dupIds(updates.rejected, "kb_updates_cumulative.rejected", ["proposal_id"], report);
    scanSummary(updates, "kb_updates_cumulative", report);
  }
  if (changelog) {
    if (!Array.isArray(changelog.applied)) push(report, "errors", "unsupported_schema", "kb_changelog.applied", "applied must be an array.");
    else dupIds(changelog.applied, "kb_changelog.applied", ["update_id", "id"], report);
    if (!Array.isArray(changelog.entries)) push(report, "errors", "unsupported_schema", "kb_changelog.entries", "entries must be an array.");
    else dupIds(changelog.entries, "kb_changelog.entries", ["update_id", "id", "tag"], report);
    scanSummary(changelog, "kb_changelog", report);
  }
}
function markdownFiles(manifest) {
  return Object.entries(manifest.files || {}).filter(([file, meta]) => {
    if (!file.endsWith(".md")) return false;
    if (file === "README.md") return false;
    if (file === "CHANGELOG.md") return true;
    return meta && (meta.public_surface === true || meta.release_review === true);
  });
}
function extractLabeledVersion(raw, label) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = raw.match(new RegExp("\\*\\*" + escaped + ":\\*\\*\\s*([^\\r\\n]+)", "m"));
  return match ? extractSemver(match[1]) : null;
}
function extractTitleVersion(raw) {
  const match = raw.match(new RegExp(`^#\\s+.*?\\bv${SEMVER}`, "m"));
  return match ? match[1] : null;
}
function extractSignatureTokenVersion(raw) {
  const match = raw.match(new RegExp(`#ATLAS-SIG-[A-Z-]+-v${SEMVER}`));
  return match ? match[1] : null;
}
function extractChangelogTopVersion(raw) {
  const match = raw.match(new RegExp(`^##\\s+v${SEMVER}\\b`, "m"));
  return match ? match[1] : null;
}
function validateMarkdownSurfaces(manifest, report) {
  markdownFiles(manifest).forEach(([file, meta]) => {
    report.files_checked.push(file);
    const raw = readText(file, report);
    if (raw == null) return;
    if (file === "CHANGELOG.md") {
      const topVersion = extractChangelogTopVersion(raw);
      if (!topVersion) push(report, "errors", "changelog_version_missing", file, "CHANGELOG.md is missing a parsable top release heading like `## vX.Y.Z`.");
      else if (topVersion !== manifest.version) push(report, "errors", "changelog_version_mismatch", file, `Top changelog version ${topVersion} does not match manifest.version ${manifest.version}.`);
      return;
    }
    const version = extractLabeledVersion(raw, "Version");
    const packageAlignment = extractLabeledVersion(raw, "Package Alignment");
    const titleVersion = extractTitleVersion(raw);
    const signatureVersion = extractSignatureTokenVersion(raw);
    if (!version) push(report, "errors", "markdown_version_missing", file, "Release-reviewed markdown surface is missing a parsable **Version:** marker.");
    else if (meta.version && version !== meta.version) push(report, "errors", "markdown_version_mismatch", file, `Surface version ${version} does not match manifest declaration ${meta.version}.`);
    if (titleVersion && version && titleVersion !== version) push(report, "errors", "markdown_title_version_mismatch", file, `Title version ${titleVersion} does not match markdown version ${version}.`);
    if (meta.package_alignment_required !== false) {
      if (!packageAlignment) push(report, "errors", "markdown_package_alignment_missing", file, "Release-reviewed markdown surface is missing a parsable **Package Alignment:** marker.");
      else if (packageAlignment !== manifest.version) push(report, "errors", "markdown_package_alignment_mismatch", file, `Package Alignment ${packageAlignment} does not match manifest.version ${manifest.version}.`);
    }
    if (signatureVersion && version && signatureVersion !== version) push(report, "errors", "markdown_signature_version_drift", file, `Signature token ${signatureVersion} does not match markdown version ${version}.`);
  });
}
function validateGitSignature(opt, report) {
  if (!opt.verifyGitSignature) return;
  const result = verifyGitReleaseSignature({ allowDirty: opt.allowDirtyGitSignature });
  if (result.commit) {
    report.git_signature = {
      ref: result.ref,
      commit: result.commit,
      signer: result.signer || null,
      signer_key: result.actualKey || null,
      expected_key: result.expectedKey || null,
      expected_email: result.expectedEmail || null,
      tags: result.tags || []
    };
  }
  result.errors.forEach((entry) => push(report, "errors", entry.code, entry.location, entry.message));
  result.warnings.forEach((entry) => push(report, "warnings", entry.code, entry.location, entry.message));
}
function validateNormalizedLedger(report) {
  const result = spawnSync("node", ["scripts/normalize_updates.js", "--dry-run", "--json"], { cwd: ROOT, encoding: "utf8" });
  if (result.error || result.status !== 0) {
    const message = (result.error && result.error.message) || result.stderr || result.stdout || "Could not verify normalized ledger state.";
    push(report, "errors", "normalize_updates_check_failed", "scripts/normalize_updates.js", message.trim());
    return;
  }
  let summary;
  try {
    summary = JSON.parse(result.stdout);
  } catch (error) {
    push(report, "errors", "normalize_updates_parse_failed", "scripts/normalize_updates.js", error.message);
    return;
  }
  if (summary && Array.isArray(summary.changes) && summary.changes.length > 0) {
    summary.changes.forEach((entry) => {
      push(report, "errors", "ledger_not_normalized", entry.location || "kb_updates_cumulative.json", entry.reason || "Ledger normalization drift detected.");
    });
  }
}
function render(report) {
  const lines = [`Overall status: ${report.errors.length ? "FAIL" : "PASS"}`, `Files checked (${report.files_checked.length}): ${report.files_checked.join(", ")}`];
  if (report.git_signature) {
    lines.push(`Git signature ref: ${report.git_signature.ref}`);
    lines.push(`Git signature commit: ${report.git_signature.commit}`);
    lines.push(`Git signer: ${report.git_signature.signer || "<unknown>"}`);
    lines.push(`Git signer key: ${report.git_signature.signer_key || "<unknown>"}`);
  }
  lines.push(`Errors: ${report.errors.length}`);
  report.errors.forEach((entry) => lines.push(`- [${entry.code}] ${entry.location}: ${entry.message}`));
  lines.push(`Warnings: ${report.warnings.length}`);
  report.warnings.forEach((entry) => lines.push(`- [${entry.code}] ${entry.location}: ${entry.message}`));
  return lines.join("\n");
}

(function main() {
  const opt = args(process.argv);
  const report = { errors: [], warnings: [], files_checked: [] };
  const loaded = {};
  JSON_FILES.forEach((file) => {
    const value = readJson(file, report);
    report.files_checked.push(file);
    if (value && value.data) {
      loaded[file] = value.data;
      scanTiers(value.data, path.basename(file, ".json"), report);
    }
  });
  const manifest = loaded["manifest.json"];
  const markdownPaths = manifest ? markdownFiles(manifest).map(([file]) => file) : [];
  const dirty = dirtyFiles([...JSON_FILES, ...markdownPaths], report);
  validateVersions(loaded, report);
  JSON_FILES.forEach((file) => loaded[file] && validateSignatures(file, loaded[file], dirty, report));
  validateTextSurfaces(report);
  if (loaded["sources.json"] && loaded["knowledge_base_merged_v2.json"]) {
    const ids = registry(loaded["sources.json"], report);
    const refs = scanCitations(loaded["knowledge_base_merged_v2.json"], ids.quar, report);
    [...refs.cited].filter((id) => !ids.top.has(id) && !ids.quar.has(id)).sort().forEach((id) => push(report, "errors", "missing_source_id", "knowledge_base_merged_v2.json", `Missing source ID ${id}.`));
    refs.surfaced.forEach((id) => push(report, "errors", "quarantined_in_surfaced", "knowledge_base_merged_v2.json", `Quarantined source ${id} is cited in surfaced content.`));
  }
  validateLedgers(loaded, report);
  validateNormalizedLedger(report);
  if (manifest) validateMarkdownSurfaces(manifest, report);
  validateGitSignature(opt, report);
  const summary = {
    status: report.errors.length ? "fail" : "pass",
    files_checked: report.files_checked,
    counts: { errors: report.errors.length, warnings: report.warnings.length },
    errors: report.errors,
    warnings: report.warnings
  };
  if (report.git_signature) summary.git_signature = report.git_signature;
  process.stdout.write(opt.json ? JSON.stringify(summary, null, 2) + "\n" : render(report) + "\n");
  process.exit(report.errors.length ? 1 : 0);
})();
