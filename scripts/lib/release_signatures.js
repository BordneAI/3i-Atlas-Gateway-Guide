const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..", "..");
const SIGNATURE_BLOCK_KEYS = new Set([
  "signature",
  "signature_footer",
  "signature_status",
  "signature_validated_at",
  "validated_by",
  "validation_basis",
  "fingerprint_sha256",
  "fingerprint_method"
]);

const JSON_SURFACES = {
  "manifest.json": { token: "MANIFEST" },
  "knowledge_base_merged_v2.json": {
    token: "KB",
    footer: (version, date) => `© BordneAI – 3i/ATLAS Gateway Guide v${version} | CC BY-NC-SA 4.0 | #ATLAS-SIG-KB-v${version}-Δ${date}`
  },
  "kb_updates_cumulative.json": {
    token: "UPDATES",
    footer: (version, date) => `© BordneAI – 3i/ATLAS Gateway Guide v${version} | CC BY-NC-SA 4.0 | #ATLAS-SIG-UPDATES-v${version}-Δ${date}`
  },
  "kb_changelog.json": {
    token: "KB-CHANGELOG",
    footer: (version, date) => `© BordneAI – 3i/ATLAS Gateway Guide v${version} | CC BY-NC-SA 4.0 | #ATLAS-SIG-KB-CHANGELOG-v${version}-Δ${date}`
  },
  "sources.json": {
    token: "SOURCES",
    footer: (version, date) => `© BordneAI – 3i/ATLAS Gateway Guide v${version} | CC BY-NC-SA 4.0 | #ATLAS-SIG-SOURCES-v${version}-Δ${date}`
  },
  "tags_index.json": {
    token: "TAGS",
    footer: (version) => `© BordneAI – 3i/ATLAS Gateway Guide v${version} | CC BY-NC-SA 4.0 | #ATLAS-SIG-TAGS-v${version}-FINGERPRINT`
  },
  "conversation_starters.json": {
    token: "CONVSTART",
    footer: (version, date) => `© 2026 BordneAI – 3i/ATLAS Gateway Guide v${version} | CC BY-NC-SA 4.0 | #ATLAS-SIG-CONVSTART-v${version}-Δ${date}`
  },
  "stress_test_framework.json": { token: "STF" },
  "bayesian_framework.json": { token: "BAYESIAN" }
};

const TEXT_SURFACES = {
  "instructions.txt": {
    token: "INSTRUCTIONS",
    versionRegex: /System Instructions \(v(\d+\.\d+\.\d+)\)/,
    apply(text, ctx) {
      let next = text;
      next = replaceLine(next, /^Signature:\s*.*$/m, `Signature: ${ctx.signature}`);
      next = replaceLine(next, /^Signature Status:\s*.*$/m, "Signature Status: signature_validated");
      next = replaceLine(next, /^signature:\s*\".*\"$/m, `signature: \"${ctx.signature}\"`);
      next = replaceLine(next, /^signature_status:\s*\".*\"$/m, 'signature_status: "signature_validated"');
      next = replaceLine(next, /^signature_validated_at:\s*\".*\"$/m, `signature_validated_at: \"${ctx.iso}\"`);
      next = replaceLine(next, /^validated_by:\s*\".*\"$/m, `validated_by: \"${ctx.validatedBy}\"`);
      return next;
    }
  },
  "BOOTLOADER.md": {
    token: "BOOT",
    versionRegex: /\*\*Version:\*\*\s*(\d+\.\d+\.\d+)/,
    apply(text, ctx) {
      let next = text;
      next = replaceLine(next, /^Signature Status:\s*.*$/m, "Signature Status: signature_validated  ");
      next = replaceLine(next, /^Signature\s+#ATLAS-SIG-BOOT-v.*$/m, `Signature ${ctx.signature}`);
      return next;
    }
  }
};

function replaceLine(text, regex, replacement) {
  return regex.test(text) ? text.replace(regex, replacement) : text;
}
function sortValue(value) {
  if (Array.isArray(value)) return value.map(sortValue);
  if (value && typeof value === "object") {
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = sortValue(value[key]);
    return out;
  }
  return value;
}
function computeFingerprint(obj) {
  const filtered = {};
  for (const key of Object.keys(obj)) {
    if (!SIGNATURE_BLOCK_KEYS.has(key)) filtered[key] = obj[key];
  }
  const canonical = JSON.stringify(sortValue(filtered));
  return crypto.createHash("sha256").update(canonical).digest("hex");
}
function buildSignature(token, version, date) {
  return `#ATLAS-SIG-${token}-v${version}-Δ${date}`;
}
function isoDateParts(now = new Date()) {
  return { iso: now.toISOString(), date: now.toISOString().slice(0, 10) };
}
function readJson(filePath) { return JSON.parse(fs.readFileSync(filePath, "utf8")); }
function writeJson(filePath, value) { fs.writeFileSync(filePath, JSON.stringify(value, null, 2) + "\n", "utf8"); }
function getDirtyFiles(files) {
  const result = spawnSync("git", ["status", "--porcelain", "--", ...files], { cwd: ROOT, encoding: "utf8" });
  if (result.error || result.status !== 0) return new Set();
  const dirty = new Set();
  result.stdout.split(/\r?\n/).filter(Boolean).forEach((line) => dirty.add(line.slice(3).trim().replace(/\\/g, "/")));
  return dirty;
}
function refreshJsonSurface(file, options = {}) {
  const config = JSON_SURFACES[file];
  const fullPath = path.join(ROOT, file);
  const data = readJson(fullPath);
  const version = data.version;
  if (typeof version !== "string" || !version.trim()) throw new Error(`${file} is missing a usable version.`);
  const { iso, date } = options.time || isoDateParts();
  const validatedBy = options.validatedBy || `ATLAS-Local-Sign-v${version}`;
  const signature = buildSignature(config.token, version, date);
  const before = JSON.stringify(data);
  data.signature = signature;
  data.signature_status = "signature_validated";
  if (Object.prototype.hasOwnProperty.call(data, "signature_footer") && typeof config.footer === "function") data.signature_footer = config.footer(version, date);
  if (Object.prototype.hasOwnProperty.call(data, "signature_validated_at")) data.signature_validated_at = iso;
  if (Object.prototype.hasOwnProperty.call(data, "validated_by")) data.validated_by = validatedBy;
  if (Object.prototype.hasOwnProperty.call(data, "validation_basis")) data.validation_basis = `Local signature refresh via scripts/refresh_release_signatures.js using sha256_canonical_json_excluding_signature_block at ${iso}.`;
  if (Object.prototype.hasOwnProperty.call(data, "fingerprint_method")) data.fingerprint_method = "sha256_canonical_json_excluding_signature_block";
  if (Object.prototype.hasOwnProperty.call(data, "fingerprint_sha256")) data.fingerprint_sha256 = computeFingerprint(data);
  const after = JSON.stringify(data);
  return { changed: before !== after, data, fullPath, version, signature };
}
function refreshTextSurface(file, options = {}) {
  const config = TEXT_SURFACES[file];
  const fullPath = path.join(ROOT, file);
  const text = fs.readFileSync(fullPath, "utf8");
  const match = text.match(config.versionRegex);
  if (!match) throw new Error(`${file} is missing a recognizable version marker.`);
  const version = match[1];
  const { iso, date } = options.time || isoDateParts();
  const validatedBy = options.validatedBy || `ATLAS-Local-Sign-v${version}`;
  const signature = buildSignature(config.token, version, date);
  const next = config.apply(text, { date, iso, signature, validatedBy, version });
  return { changed: text !== next, text: next, fullPath, version, signature };
}
module.exports = {
  ROOT,
  JSON_SURFACES,
  TEXT_SURFACES,
  SIGNATURE_BLOCK_KEYS,
  buildSignature,
  computeFingerprint,
  getDirtyFiles,
  isoDateParts,
  refreshJsonSurface,
  refreshTextSurface,
  writeJson
};
