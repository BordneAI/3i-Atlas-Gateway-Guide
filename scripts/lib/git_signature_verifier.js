const { spawnSync } = require("child_process");
const { ROOT } = require("./release_signatures");

function runGit(args) {
  const result = spawnSync("git", args, { cwd: ROOT, encoding: "utf8" });
  return {
    args,
    status: typeof result.status === "number" ? result.status : 1,
    stdout: result.stdout || "",
    stderr: result.stderr || "",
    error: result.error || null
  };
}

function gitConfig(name) {
  const result = runGit(["config", "--get", name]);
  if (result.error || result.status !== 0) return null;
  const value = result.stdout.trim();
  return value || null;
}

function normalizeKey(value) {
  return typeof value === "string" ? value.replace(/\s+/g, "").toUpperCase() : null;
}

function keysMatch(expected, actual) {
  const left = normalizeKey(expected);
  const right = normalizeKey(actual);
  if (!left || !right) return false;
  return left === right || left.endsWith(right) || right.endsWith(left);
}

function parseSignatureOutput(text) {
  const actualKey =
    (text.match(/using [A-Z0-9-]+ key ([A-F0-9]{8,40})/i) || [])[1] ||
    (text.match(/Primary key fingerprint:\s*([A-F0-9 ]{20,60})/i) || [])[1]?.replace(/\s+/g, "");
  const signerLine = (text.match(/Good signature from "([^"]+)"/) || [])[1] || null;
  const signerEmail = (signerLine && (signerLine.match(/<([^>]+)>/) || [])[1]) || null;
  return {
    actualKey: normalizeKey(actualKey),
    signerLine,
    signerEmail
  };
}

function verifyGitReleaseSignature(options = {}) {
  const ref = options.ref || "HEAD";
  const expectedKey = options.expectedKey || gitConfig("user.signingkey");
  const expectedEmail = options.expectedEmail || gitConfig("user.email");
  const requireClean = options.allowDirty ? false : true;
  const errors = [];
  const warnings = [];

  const rev = runGit(["rev-parse", ref]);
  if (rev.error || rev.status !== 0) {
    errors.push({
      code: "git_ref_unresolved",
      location: ref,
      message: `Could not resolve git ref ${ref}.`
    });
    return { ok: false, ref, errors, warnings };
  }
  const commit = rev.stdout.trim();

  const status = runGit(["status", "--porcelain"]);
  const dirtyEntries = status.error || status.status !== 0
    ? []
    : status.stdout.split(/\r?\n/).filter(Boolean);
  if ((status.error || status.status !== 0) && requireClean) {
    warnings.push({
      code: "git_status_unavailable",
      location: "git status --porcelain",
      message: "Could not determine worktree cleanliness while verifying Git signature."
    });
  }
  if (requireClean && dirtyEntries.length > 0) {
    errors.push({
      code: "worktree_dirty",
      location: "git status --porcelain",
      message: "Working tree is dirty; verify the signed release commit/tag from a clean state or rerun with --allow-dirty for signer inspection only."
    });
  }

  const verify = runGit(["verify-commit", ref]);
  if (verify.error || verify.status !== 0) {
    errors.push({
      code: "git_commit_signature_invalid",
      location: ref,
      message: (verify.stderr || verify.stdout || "git verify-commit failed.").trim()
    });
    return { ok: false, ref, commit, expectedKey, expectedEmail, errors, warnings };
  }

  const show = runGit(["log", "--show-signature", "-1", "--format=fuller", ref]);
  if (show.error || show.status !== 0) {
    errors.push({
      code: "git_signature_inspection_failed",
      location: ref,
      message: (show.stderr || show.stdout || "git log --show-signature failed.").trim()
    });
    return { ok: false, ref, commit, expectedKey, expectedEmail, errors, warnings };
  }

  const parsed = parseSignatureOutput(show.stdout);
  if (!parsed.actualKey) {
    errors.push({
      code: "git_signature_key_missing",
      location: ref,
      message: "Could not parse the signing key fingerprint from git signature output."
    });
  }
  if (!parsed.signerLine) {
    errors.push({
      code: "git_signature_identity_missing",
      location: ref,
      message: "Could not parse the signer identity from git signature output."
    });
  }
  if (expectedKey && parsed.actualKey && !keysMatch(expectedKey, parsed.actualKey)) {
    errors.push({
      code: "git_signing_key_mismatch",
      location: ref,
      message: `Git commit was signed by key ${parsed.actualKey}, but git config user.signingkey is ${expectedKey}.`
    });
  }
  if (!expectedKey) {
    warnings.push({
      code: "git_signing_key_unconfigured",
      location: "git config user.signingkey",
      message: "No git signing key is configured; signer verification can only rely on the signature output."
    });
  }
  if (expectedEmail && parsed.signerEmail && expectedEmail.toLowerCase() !== parsed.signerEmail.toLowerCase()) {
    errors.push({
      code: "git_signer_email_mismatch",
      location: ref,
      message: `Git commit was signed by ${parsed.signerEmail}, but git config user.email is ${expectedEmail}.`
    });
  }
  if (!expectedEmail) {
    warnings.push({
      code: "git_signer_email_unconfigured",
      location: "git config user.email",
      message: "No git user.email is configured; signer verification cannot confirm email identity."
    });
  }

  const tags = runGit(["tag", "--points-at", ref]);
  const tagNames = tags.error || tags.status !== 0
    ? []
    : tags.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);

  return {
    ok: errors.length === 0,
    ref,
    commit,
    expectedKey,
    expectedEmail,
    actualKey: parsed.actualKey,
    signer: parsed.signerLine,
    signerEmail: parsed.signerEmail,
    tags: tagNames,
    errors,
    warnings
  };
}

module.exports = {
  gitConfig,
  keysMatch,
  normalizeKey,
  parseSignatureOutput,
  runGit,
  verifyGitReleaseSignature
};
