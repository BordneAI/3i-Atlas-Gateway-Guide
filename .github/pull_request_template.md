## Summary

Describe the change clearly and factually.

## Change Type

- [ ] KB/content update
- [ ] Release/process update
- [ ] Validation/tooling update
- [ ] Docs/community standards update
- [ ] Bug fix

## Files Touched

List the main files changed.

## Provenance and Safety Check

- [ ] No fabricated sources, citations, signatures, or validation events
- [ ] No speculative AAIV/T4 material promoted as fact
- [ ] Stale operational guidance is archived or clearly marked non-current where applicable
- [ ] Internal audit notes are kept separate from scientific claims where applicable

## Release Surface Review

If this PR touches release surfaces:

- [ ] `manifest.json` reviewed
- [ ] `instructions.txt` reviewed if package/release behavior changed
- [ ] `CHANGELOG.md` reviewed if release history changed
- [ ] manifest-listed `docs/` surfaces reviewed if package alignment changed
- [ ] governance/support surfaces reviewed if affected (`BOOTLOADER.md`, `PROMPTS/guardian_prompt.md`, `conversation_starters.json`, `stress_test_framework.json`)

## Validation

List the commands you actually ran and the real results.

```text
node scripts/validate_kb.js
node scripts/refresh_release_signatures.js --all --write
node scripts/verify_release_git_signature.js --allow-dirty
```

## Notes for Reviewers

Call out any intentional non-changes, schema constraints, or follow-up work.
