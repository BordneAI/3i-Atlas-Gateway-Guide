# Contributing to 3i/ATLAS Gateway Guide

Thank you for contributing to the official repository for the public CustomGPT **3i/ATLAS Gateway Guide**.

This repository is not a generic app codebase. It is a governed knowledge and release surface for a public-facing GPT. Contributions therefore need to preserve provenance, release integrity, and safety guardrails.

## Before You Contribute

Please read these files first:

- `README.md`
- `SECURITY.md`
- `instructions.txt`
- `manifest.json`

Canonical release truth is defined by:

- `manifest.json`
- `instructions.txt`
- `CHANGELOG.md`

If another file disagrees with those surfaces, treat the canonical surfaces as authoritative.

## Ground Rules

All contributions should follow these rules:

- no fabricated sources, citations, signatures, fingerprints, or validation events
- no speculative AAIV/T4 material promoted as T1/T2 fact
- no weakening of provenance tiering or safety rules without explicit justification
- no stale operational guidance presented as current
- no unrelated file churn in focused pull requests

## Types of Contributions

Useful contributions include:

- source-backed KB updates
- provenance and citation cleanup
- validator and release-process hardening
- docs improvements that preserve current governance rules
- test and workflow improvements for release safety

## Branching and Scope

Prefer small, focused branches and pull requests.

Keep one PR to one primary purpose, for example:

- KB patch release
- validator/process repair
- docs/community standards update

Avoid mixing release-content edits with unrelated editor or workspace changes.

## Knowledge Base and Source Changes

When editing KB or source surfaces:

- include exact source IDs
- use explicit ISO dates where the schema supports them
- preserve stronger existing fields unless a source-backed update supersedes them
- demote stale content instead of deleting it when the schema allows archival handling
- keep internal audit notes separate from scientific claims

If a source URL is not present in the approved package material, do not invent one.

## Release Surface Expectations

A version bump or patch integration should review the manifest-listed release surfaces, including:

- `manifest.json`
- `knowledge_base_merged_v2.json`
- `sources.json`
- `kb_updates_cumulative.json`
- `kb_changelog.json`
- `tags_index.json`
- `instructions.txt`
- `CHANGELOG.md`
- `README.md`
- `BOOTLOADER.md`
- `PROMPTS/guardian_prompt.md`
- manifest-listed `docs/` surfaces
- related public support surfaces such as `conversation_starters.json` and `stress_test_framework.json`

## Validation

Run the relevant checks before opening a PR:

```powershell
node scripts/validate_kb.js
node scripts/refresh_release_signatures.js --all --write
node scripts/verify_release_git_signature.js --allow-dirty
```

Use the strict Git signature check from a clean tree before final release/tag work:

```powershell
node scripts/verify_release_git_signature.js
```

If your change touches only a subset of release surfaces, scope your review accordingly, but do not claim a sealed or validated state without running the real checks.

## Commit and PR Guidance

Use clear commit messages that describe what changed.

Examples:

- `Docs: add GitHub community standard files`
- `Release: integrate v2.12.4 cumulative patch`
- `Validation: harden release-aware ledger checks`

In your PR, state:

- what changed
- why it changed
- which files were intentionally left untouched
- which validation commands were run and their real results

## Security and Sensitive Issues

If you find a vulnerability, prompt-injection path, governance bypass, or misinformation/safety failure, follow `SECURITY.md` instead of opening a normal public bug report.

## Questions

If you are unsure whether a change belongs in a patch release, a process PR, or a docs-only PR, default to the smaller and safer scope.
