#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const P = {
  manifest: path.join(ROOT, "manifest.json"),
  updates: path.join(ROOT, "kb_updates_cumulative.json"),
  changelog: path.join(ROOT, "kb_changelog.json")
};
const SUPPORTED = /^2\.12\.\d+$/;
const FLAGS = new Set(["--dry-run", "--write", "--json", "--help"]);

function usage(code = 0) {
  const out = code === 0 ? process.stdout : process.stderr;
  out.write("Usage: node normalize_updates.js --dry-run|--write [--json]\n");
  process.exit(code);
}
function parseArgs(argv) {
  const flags = argv.slice(2);
  for (const flag of flags) if (!FLAGS.has(flag)) usage(1);
  if (flags.includes("--help")) usage(0);
  const dry = flags.includes("--dry-run");
  const write = flags.includes("--write");
  if (dry === write) usage(1);
  return { json: flags.includes("--json"), mode: dry ? "dry-run" : "write" };
}
function readJson(file) { return JSON.parse(fs.readFileSync(file, "utf8")); }
function saveJson(file, value) {
  const raw = JSON.stringify(value, null, 2) + "\n";
  const tmp = `${file}.tmp`;
  fs.writeFileSync(tmp, raw, "utf8");
  fs.renameSync(tmp, file);
}
function clone(value) { return JSON.parse(JSON.stringify(value)); }
function same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
function push(report, level, code, location, message) { report[level].push({ code, location, message }); }
function change(report, location, before, after, reason) { report.changes.push({ location, before, after, reason }); }
function dedupe(list) {
  const seen = new Set();
  return list.filter((item) => (seen.has(item) ? false : (seen.add(item), true)));
}
function normDomain(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  const trimmed = value.trim();
  try {
    const url = new URL(trimmed.includes("://") ? trimmed : `https://${trimmed}`);
    return url.hostname.toLowerCase() || null;
  } catch {
    return /^[A-Za-z0-9.-]+$/.test(trimmed) ? trimmed.toLowerCase() : null;
  }
}
function normArray(item, field, loc, report, map = (v) => v, sort = false) {
  if (!(field in item)) return;
  if (!Array.isArray(item[field])) return push(report, "errors", "field_not_array", `${loc}.${field}`, `${field} must be an array.`);
  const next = [];
  for (let i = 0; i < item[field].length; i += 1) {
    const value = item[field][i];
    if (typeof value !== "string") return push(report, "errors", "non_string_array_value", `${loc}.${field}[${i}]`, `${field} must contain only strings.`);
    const mapped = map(value);
    if (mapped == null || mapped === "") return push(report, "errors", "array_value_not_normalizable", `${loc}.${field}[${i}]`, `Could not normalize ${field}.`);
    next.push(mapped);
  }
  const finalList = dedupe(next);
  if (sort) finalList.sort();
  if (!same(item[field], finalList)) {
    const before = item[field];
    item[field] = finalList;
    change(report, `${loc}.${field}`, before, finalList, "Normalized deterministic string array.");
  }
}
function inferRejected(item) { return item && item.decision === "DEFER_WITH_NEW_DUE_DATE" ? "deferred" : "closed_no_action"; }
function normStatus(item, bucket, loc, report) {
  const allowed = { pending: new Set(["pending"]), integrated: new Set(["integrated"]), rejected: new Set(["closed_no_action", "deferred"]) };
  if (bucket === "pending" && (item.integrated_at || item.integrated_to)) return push(report, "errors", "pending_history_fields_present", loc, "Pending entries may not carry integrated history fields.");
  const fallback = bucket === "pending" ? "pending" : bucket === "integrated" ? "integrated" : inferRejected(item);
  if (item.status == null) {
    item.status = fallback;
    return change(report, `${loc}.status`, null, fallback, "Filled missing supported status.");
  }
  if (typeof item.status !== "string" || !item.status.trim()) return push(report, "errors", "status_not_string", `${loc}.status`, "Status must be a non-empty string.");
  const next = item.status.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (!allowed[bucket].has(next)) return push(report, "errors", "unsupported_status", `${loc}.status`, `Unsupported status ${item.status} for ${bucket}.`);
  if (next !== item.status) {
    const before = item.status;
    item.status = next;
    change(report, `${loc}.status`, before, next, "Normalized supported status token.");
  }
}
function validateRepo(manifest, updates, changelog, report) {
  const mv = manifest && manifest.version;
  if (!SUPPORTED.test(mv || "")) push(report, "errors", "unsupported_version", "manifest.version", `Only 2.12.x repos are supported; found ${mv || "<missing>"}.`);
  const checks = [
    [updates.version, "kb_updates_cumulative.version"],
    [updates.updates_version, "kb_updates_cumulative.updates_version"],
    [changelog.version, "kb_changelog.version"],
    [changelog.changelog_version, "kb_changelog.changelog_version"]
  ];
  for (const [value, label] of checks) if (value !== mv) push(report, "errors", "version_mismatch", label, `${label} must match manifest.version (${mv}).`);
  for (const key of ["pending", "integrated", "rejected"]) if (!Array.isArray(updates[key])) push(report, "errors", "unsupported_schema", key, `${key} must be an array.`);
  if (!updates.continuity_metrics || typeof updates.continuity_metrics !== "object") push(report, "errors", "unsupported_schema", "continuity_metrics", "continuity_metrics must be present.");
  if (!Array.isArray(changelog.applied)) push(report, "errors", "unsupported_schema", "kb_changelog.applied", "kb_changelog.applied must be an array.");
}
function dupProposalIds(updates, report) {
  const seen = new Map();
  for (const bucket of ["pending", "integrated", "rejected"]) {
    for (let i = 0; i < updates[bucket].length; i += 1) {
      const id = updates[bucket][i] && updates[bucket][i].proposal_id;
      if (typeof id !== "string" || !id.trim()) continue;
      const loc = `${bucket}[${i}].proposal_id`;
      if (!seen.has(id)) seen.set(id, []);
      seen.get(id).push(loc);
    }
  }
  for (const [id, locations] of seen.entries()) if (locations.length > 1) push(report, "errors", "duplicate_proposal_id", locations.join(", "), `Duplicate proposal_id ${id}.`);
}
function refreshMetrics(updates, report) {
  const items = [...updates.pending, ...updates.integrated, ...updates.rejected];
  const weights = items.map((item) => item && item.continuity_weight).filter((value) => typeof value === "number" && Number.isFinite(value));
  const target = {
    average_continuity_weight: weights.length ? Number((weights.reduce((a, b) => a + b, 0) / weights.length).toFixed(4)) : updates.continuity_metrics.average_continuity_weight,
    integration_ratio: items.length ? Number((updates.integrated.length / items.length).toFixed(4)) : 0,
    total_integrated: updates.integrated.length,
    total_pending: updates.pending.length,
    total_rejected: updates.rejected.length,
    total_tracked: items.length
  };
  for (const [key, value] of Object.entries(target)) {
    if (!same(updates.continuity_metrics[key], value)) {
      const before = updates.continuity_metrics[key];
      updates.continuity_metrics[key] = value;
      change(report, `continuity_metrics.${key}`, before, value, "Refreshed derived continuity metric.");
    }
  }
}
function checkRefs(updates, changelog, report) {
  const applied = new Set(changelog.applied.map((entry) => entry && (entry.update_id || entry.id)).filter(Boolean));
  updates.integrated.forEach((item, index) => {
    if (!item || typeof item.integrated_to !== "string") return;
    const match = item.integrated_to.match(/entry:\s*([^\s,]+)/i);
    if (match && !applied.has(match[1])) push(report, "warnings", "missing_changelog_reference", `integrated[${index}].integrated_to`, `Missing kb_changelog.applied ID ${match[1]}.`);
  });
}
function render(report) {
  const lines = [
    `normalize_updates.js (${report.mode})`,
    `Files checked: ${report.filesChecked.join(", ")}`,
    `Changes ${report.mode === "write" ? "applied" : "planned"}: ${report.changes.length}`
  ];
  report.changes.forEach((entry) => lines.push(`- ${entry.location}: ${entry.reason}`));
  lines.push(`Warnings: ${report.warnings.length}`);
  report.warnings.forEach((entry) => lines.push(`- [${entry.code}] ${entry.location}: ${entry.message}`));
  lines.push(`Errors: ${report.errors.length}`);
  report.errors.forEach((entry) => lines.push(`- [${entry.code}] ${entry.location}: ${entry.message}`));
  return lines.join("\n");
}

(function main() {
  const opts = parseArgs(process.argv);
  const report = { changes: [], errors: [], filesChecked: ["manifest.json", "kb_updates_cumulative.json", "kb_changelog.json"], mode: opts.mode, warnings: [] };
  let manifest, updates, changelog;
  try {
    manifest = readJson(P.manifest);
    updates = readJson(P.updates);
    changelog = readJson(P.changelog);
  } catch (error) {
    push(report, "errors", "json_load_failed", "load", error.message);
  }
  if (report.errors.length === 0) validateRepo(manifest, updates, changelog, report);
  const next = report.errors.length === 0 ? clone(updates) : null;
  if (next) {
    for (const bucket of ["pending", "integrated", "rejected"]) {
      next[bucket].forEach((item, index) => {
        const loc = `${bucket}[${index}]`;
        normStatus(item, bucket, loc, report);
        normArray(item, "approval_requirements", loc, report);
        normArray(item, "proposal_tier_mix", loc, report);
        normArray(item, "required_domains", loc, report, normDomain, true);
        normArray(item, "review_checklist", loc, report);
        normArray(item, "source_ids_proposed", loc, report);
      });
    }
    dupProposalIds(next, report);
    refreshMetrics(next, report);
    checkRefs(next, changelog, report);
  }
  const summary = { status: report.errors.length ? "failed" : "ok", mode: report.mode, files_checked: report.filesChecked, counts: { changes: report.changes.length, errors: report.errors.length, warnings: report.warnings.length }, changes: report.changes, warnings: report.warnings, errors: report.errors };
  if (report.errors.length === 0 && opts.mode === "write" && report.changes.length) saveJson(P.updates, next);
  process.stdout.write(opts.json ? JSON.stringify(summary, null, 2) + "\n" : render(report) + "\n");
  process.exit(report.errors.length ? 1 : 0);
})();