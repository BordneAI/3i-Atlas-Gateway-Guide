#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const {
  ROOT,
  JSON_SURFACES,
  TEXT_SURFACES,
  getDirtyFiles,
  isoDateParts,
  refreshJsonSurface,
  refreshTextSurface,
  writeJson
} = require("./lib/release_signatures");

const FLAGS = new Set(["--dry-run", "--write", "--all", "--json", "--help"]);

function usage(code = 0) {
  const out = code === 0 ? process.stdout : process.stderr;
  out.write([
    "Usage:",
    "  node scripts/refresh_release_signatures.js --dry-run [--all] [--files file1,file2] [--validated-by NAME] [--json]",
    "  node scripts/refresh_release_signatures.js --write [--all] [--files file1,file2] [--validated-by NAME] [--json]"
  ].join("\n") + "\n");
  process.exit(code);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  const out = { json: false, mode: null, all: false, files: null, validatedBy: null };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (FLAGS.has(arg)) {
      if (arg === "--dry-run") out.mode = out.mode ? null : "dry-run";
      if (arg === "--write") out.mode = out.mode ? null : "write";
      if (arg === "--all") out.all = true;
      if (arg === "--json") out.json = true;
      if (arg === "--help") usage(0);
      continue;
    }
    if (arg === "--files") {
      out.files = (args[i + 1] || "").split(",").map((value) => value.trim()).filter(Boolean);
      i += 1;
      continue;
    }
    if (arg === "--validated-by") {
      out.validatedBy = args[i + 1] || null;
      i += 1;
      continue;
    }
    usage(1);
  }
  if (!out.mode) usage(1);
  return out;
}

function render(result) {
  const lines = [
    `refresh_release_signatures.js (${result.mode})`,
    `Selected files: ${result.selected.length ? result.selected.join(", ") : "<none>"}`,
    `Changed files: ${result.changed.length}`
  ];
  result.changed.forEach((entry) => lines.push(`- ${entry.file}: refreshed ${entry.type} signature metadata`));
  lines.push(`Errors: ${result.errors.length}`);
  result.errors.forEach((entry) => lines.push(`- ${entry.file}: ${entry.message}`));
  return lines.join("\n");
}

(function main() {
  const opts = parseArgs(process.argv);
  const signable = [...Object.keys(JSON_SURFACES), ...Object.keys(TEXT_SURFACES)].filter((file) => fs.existsSync(path.join(ROOT, file)));
  const dirty = getDirtyFiles(signable);
  const selected = opts.files ? opts.files : opts.all ? signable : signable.filter((file) => dirty.has(file));
  const now = isoDateParts();
  const result = { mode: opts.mode, selected, changed: [], errors: [] };

  for (const file of selected) {
    try {
      if (Object.prototype.hasOwnProperty.call(JSON_SURFACES, file)) {
        const refreshed = refreshJsonSurface(file, { time: now, validatedBy: opts.validatedBy });
        if (refreshed.changed) {
          result.changed.push({ file, type: "json", signature: refreshed.signature, version: refreshed.version });
          if (opts.mode === "write") writeJson(refreshed.fullPath, refreshed.data);
        }
        continue;
      }
      if (Object.prototype.hasOwnProperty.call(TEXT_SURFACES, file)) {
        const refreshed = refreshTextSurface(file, { time: now, validatedBy: opts.validatedBy });
        if (refreshed.changed) {
          result.changed.push({ file, type: "text", signature: refreshed.signature, version: refreshed.version });
          if (opts.mode === "write") fs.writeFileSync(refreshed.fullPath, refreshed.text, "utf8");
        }
        continue;
      }
      result.errors.push({ file, message: "File is not a supported signable surface." });
    } catch (error) {
      result.errors.push({ file, message: error.message });
    }
  }

  const summary = {
    status: result.errors.length ? "failed" : "ok",
    mode: result.mode,
    selected: result.selected,
    changed: result.changed,
    errors: result.errors
  };
  process.stdout.write(opts.json ? JSON.stringify(summary, null, 2) + "\n" : render(result) + "\n");
  process.exit(result.errors.length ? 1 : 0);
})();