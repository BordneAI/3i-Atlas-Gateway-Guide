#!/usr/bin/env node
const { verifyGitReleaseSignature } = require("./lib/git_signature_verifier");

const FLAGS = new Set(["--json", "--help", "--allow-dirty"]);

function usage(code = 0) {
  const out = code === 0 ? process.stdout : process.stderr;
  out.write([
    "Usage:",
    "  node scripts/verify_release_git_signature.js [--ref REF] [--expected-key KEY] [--expected-email EMAIL] [--allow-dirty] [--json]"
  ].join("\n") + "\n");
  process.exit(code);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  const out = { json: false, allowDirty: false, ref: "HEAD", expectedKey: null, expectedEmail: null };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (FLAGS.has(arg)) {
      if (arg === "--json") out.json = true;
      if (arg === "--allow-dirty") out.allowDirty = true;
      if (arg === "--help") usage(0);
      continue;
    }
    if (arg === "--ref") {
      out.ref = args[i + 1] || null;
      i += 1;
      continue;
    }
    if (arg === "--expected-key") {
      out.expectedKey = args[i + 1] || null;
      i += 1;
      continue;
    }
    if (arg === "--expected-email") {
      out.expectedEmail = args[i + 1] || null;
      i += 1;
      continue;
    }
    usage(1);
  }
  if (!out.ref) usage(1);
  return out;
}

function render(result) {
  const lines = [
    `Overall status: ${result.ok ? "PASS" : "FAIL"}`,
    `Ref: ${result.ref}`,
    `Commit: ${result.commit || "<unresolved>"}`,
    `Signer: ${result.signer || "<unknown>"}`,
    `Signer key: ${result.actualKey || "<unknown>"}`,
    `Expected key: ${result.expectedKey || "<unconfigured>"}`,
    `Expected email: ${result.expectedEmail || "<unconfigured>"}`,
    `Tags at ref: ${result.tags && result.tags.length ? result.tags.join(", ") : "<none>"}`,
    `Errors: ${result.errors.length}`
  ];
  result.errors.forEach((entry) => lines.push(`- [${entry.code}] ${entry.location}: ${entry.message}`));
  lines.push(`Warnings: ${result.warnings.length}`);
  result.warnings.forEach((entry) => lines.push(`- [${entry.code}] ${entry.location}: ${entry.message}`));
  return lines.join("\n");
}

(function main() {
  const opts = parseArgs(process.argv);
  const result = verifyGitReleaseSignature(opts);
  const summary = {
    status: result.ok ? "pass" : "fail",
    ref: result.ref,
    commit: result.commit || null,
    signer: result.signer || null,
    signer_key: result.actualKey || null,
    expected_key: result.expectedKey || null,
    expected_email: result.expectedEmail || null,
    tags: result.tags || [],
    errors: result.errors,
    warnings: result.warnings
  };
  process.stdout.write(opts.json ? JSON.stringify(summary, null, 2) + "\n" : render(result) + "\n");
  process.exit(result.ok ? 0 : 1);
})();
