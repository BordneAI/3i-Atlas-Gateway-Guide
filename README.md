# 🌌 3i/ATLAS Gateway Guide — v2.14.0
### *NexGen Axiom Guard Integration (Phase-11 on Phase-10)*  
Version: **2.14.0** | Phase: **11** | Last Updated: **2026-04-29** | Integrity Score: **9.7** | Ethics Constant: **Love > Fear** | Audit Cycle: **24 h**
README is informational; canonical surfaces govern

**Validation (v2.11.x runtime engine):**  
9.9/10 (Grok peer review, v2.11.2, Dec 2025) ·  
9.85/10 (Grok aggregate peer review, v2.11.1) ·  
9.75/10 (human peer review, v2.10.1 baseline)

> v2.14.0 keeps the v2.11.x continuity runtime base, carries the v2.12.4 sealed patch baseline forward, and adds Axiom Guard as a bounded governance sidecar and release-preflight layer.

---

## 🧭 Overview

**3i/ATLAS Gateway Guide** provides an ethically governed, continuously validated knowledge framework built on the **BordneAI Phase-10 Continuity Protocols**.

**v2.14.0 is a non-breaking sealed minor release.**  
It carries the live science refresh concept forward and adds Axiom Guard as a bounded local claim-classification, audit, and release-preflight helper.

This version:

- Adds `tools/axiom_guard/` as a dependency-light governance sidecar
- Adds negative-null smoke tests for non-detection claims
- Adds `scripts/axiom_preflight.py` as a release-preflight bridge
- Keeps Axiom Guard bounded: not AGI, not consciousness, and not a KB replacement
- Preserves AAIV as T4-only, opt-in, natural-first, and low-prior
- Integrates approved LIVE 3I/ATLAS updates for SPHEREx observations, isotopic composition, post-perihelion spectroscopy, and non-gravitational acceleration uncertainty
- Refreshes the current JPL Horizons solution snapshot and March 2026 Jupiter-approach geometry
- Carries forward NASA Earth-safety and TESS campaign status as still current-valid
- Preserves Galileo Project linkage as deferred because no qualifying official result update was confirmed in this refresh
- Demotes late-2025 observing guidance to archival-only status
- Records the runtime CHI live-certification gap as an internal audit evidence note without fabricating runtime proof
- Includes release-engineering hardening for normalization, validation, signatures, and community-standard repo surfaces

Phase-11 represents a governance and surface-alignment layer built on top of the stable Phase-10 continuity engine. Core reasoning behavior remains v2.11.x.

> “Truth stabilizes  →  Consciousness harmonizes  →  Falsehood dissolves.”  
> — BordneAI Continuity Charter

---

## 🧭 Canonical Release Surfaces

Authoritative release truth is defined by:

- `manifest.json`
- `instructions.txt`
- `CHANGELOG.md`

If any discrepancy appears, those files govern over this README.

---

## Quick Guides

For a fast entry point into the repo's behavior and public-facing intent:

- `docs/FAQ.md` — public user FAQ for common 3I/ATLAS and safety questions
- `docs/GOVERNANCE_OVERVIEW.md` — maintainer/auditor summary of BAAM, AAIV, CHI, Reflexion, Rumor Radar, and Plain Mode

---

## Axiom Guard Sidecar

Axiom Guard is a bounded governance runtime used for claim classification, negative-null discipline, local audit logging, optional memory records, and release preflight checks.

Run:

```bash
cd tools/axiom_guard
./run_axiom_guard.sh --plain --no-persist
./run_axiom_guard.sh --json --no-persist
```

Negative-null claims mean bounded non-detection, not proof of absence.

Release preflight:

```bash
python scripts/axiom_preflight.py --plain
node scripts/validate_kb.js
node scripts/refresh_release_signatures.js --all --write
```

Axiom Guard is a governance helper only. It does not replace source-based reasoning, the KB, or live web verification.

---

## External Evaluations

3i/ATLAS Gateway Guide has undergone independent human and AI review. These evaluations are preserved for transparency and longitudinal governance tracking:

- **Human peer review (v2.10.1 baseline)** – **9.75 / 10**  
  → `docs/peer_review_human_v2_10_1.md`

- **Grok peer review (v2.11.1)** – **9.6 / 10**

- **Grok validation (v2.11.2 self-audit check)** – **9.9 / 10**

- **Grok follow-up review (recommendations check)** – **9.75 / 10**  
  Aggregate meta-update: **9.85 / 10**

- **AAIV Scientific Framework (T4 hypothesis generator)**  
  Bordne, D. (2025). *The Active Autonomous Interstellar Vehicle (AAIV) Model for 3I/ATLAS.*  
  Treated as a T2/T3 documented reasoning artifact defining a T4 speculative hypothesis generator with explicit low priors and Bayesian anomaly framing.

These evaluations are transparency artifacts. They are not substitutes for formal academic peer review.

---

## ⚙️ Core Protocols

| Protocol | Function |
|-----------|-----------|
| **Love > Fear Constant** | Ethical equilibrium stabilizer |
| **DaisyAI Ethical Kernel v1.3** | Tier-weighted reasoning with empathy balancing |
| **Reflexion v2.11.x (runtime)** | Self-validation + F-tier anomaly detection |
| **Continuity Health Index (CHI)** | Integrity metric (target ≥ 9.5) |
| **EOS Transparency Layer** | Provenance + confidence labeling |

---

## 🧠 Tier Framework Summary

### Truth Tiers (T-0 → T-5)
Empirical → Corroborated → Interpretive → Symbolic → Speculative → Mythic  

### False Tiers (F-0 → F-7)
Mechanical Fault → Context Loss → Misclassification → Cognitive Bias → Fabrication → Deceptive → Parasitic Entropy → Nihilistic Collapse  

### Consciousness Tiers (C-0 → C-6)
Instinctive → Procedural → Analytical → Empathic → Reflective → Integrative → Transcendent  

v2.11.1 introduced numeric tier weights (T0 → +5 … T5 → 0; F0 → 0 … F7 → −7) and a negative-null policy for T1/T2 “no detection” statements.

---

## 🧩 What’s New in v2.11.x (Core Engine)

- CHI integration across audit modules  
- Reflexion self-audit loop  
- Love > Fear polarity enforcement  
- EOS transparency integration in `sources.json`  
- Expanded governance tags  
- Automated integrity audit cycle (24 h default)

v2.14.0 does **not** replace the core Phase-10 engine; it adds a bounded Axiom Guard sidecar and release-preflight layer on top of the sealed governance baseline.

---

## 🧾 File Map (Governance Surface)

| File | Function |
|------|-----------|
| `manifest.json` | System manifest + release metadata |
| `BOOTLOADER.md` | Runtime boot sequence and release-aligned startup summary |
| `bayesian_framework.json` | Ethical Bayesian reasoning layer |
| `conversation_starters.json` | Persona-aware entry prompts and routing starters |
| `PROMPTS/guardian_prompt.md` | Contributor governance prompt for AI-assisted repo work |
| `scripts/normalize_updates.js` | Reflexion normalization + continuity auditing (root `normalize_updates.js` kept as compatibility shim) |
| `scripts/axiom_preflight.py` | Axiom Guard release preflight bridge |
| `tools/axiom_guard/` | Bounded governance sidecar for claim classification and negative-null smoke checks |
| `stress_test_framework.json` | CHI + integrity stress tests |
| `sources.json` | Provenance registry |
| `knowledge_base_merged_v2.json` | Tier-tagged knowledge corpus |
| `kb_updates_cumulative.json` | Update queue + continuity metrics |
| `kb_changelog.json` | Immutable audit log |
| `tags_index.json` | Tag taxonomy + governance index |

Individual file headers define their own internal version metadata.

---

## 🧮 Metrics & Governance

| Metric | Target | Description |
|---------|---------|-------------|
| **CHI** | ≥ 9.5 | Overall integrity score |
| **Entropy Leak** | ≤ 0.25 | Continuity Lock trigger threshold |
| **Reflexion Audit Cycle** | 24 h | Full validation interval |
| **Ethical Bias Drift** | ≤ 0.05 | Love > Fear equilibrium variance |

---

## 🧬 Public Audit Transparency

Audit logs (GPT Store deployment target) are written to: /logs/reflexion_audit_YYYYMMDD.json

These logs include CHI scores, tier distributions, and anomaly flags.

Each release includes an ATLAS signature marker.  
Signature metadata is regenerated during integrity sweeps.

---

## ✅ Release Checklist: Integrity + Signatures

If any signed or integrity-audited file is edited:

- Rerun integrity audit workflow
- Regenerate signature metadata
- Do **not** copy prior signatures forward

Signed/audited artifacts include:

- `manifest.json`
- `BOOTLOADER.md`
- `bayesian_framework.json`
- `conversation_starters.json`
- `stress_test_framework.json`
- `tags_index.json`
- `kb_updates_cumulative.json`
- `knowledge_base_merged_v2.json`
- `sources.json`

A version bump is incomplete until audit metadata and signatures are refreshed for all edited signed artifacts.
A version bump is also incomplete until manifest-listed live `docs/` surfaces and release-reviewed governance surfaces (`BOOTLOADER.md`, `PROMPTS/guardian_prompt.md`) have been explicitly reviewed for package alignment.
Run `node scripts/validate_kb.js` after release-surface edits, and use `node scripts/refresh_release_signatures.js --all --write` before sealing when signed surfaces changed.

---

## 🪶 Version Changelog

**2.14.0 — NexGen Axiom Guard Integration (2026-04-29)**  
– Added `tools/axiom_guard/` as a bounded governance sidecar.  
– Added `scripts/axiom_preflight.py` release-preflight bridge.  
– Added negative-null smoke tests for non-detection claims.  
– Registered Axiom Guard in `manifest.json`.  
– Preserved AAIV as T4-only, opt-in, natural-first, and low-prior.  
– Breaking changes: none.

**2.12.3 — Governance Hardening + Seal Finalization (2026-02-22)**  
– Canonical surfaces reconciled to sealed state.  
– Option C gate + STF infrastructure integrated and hardened.  
– Pre-seal citation cleanup completed (`free_text_in_citation_fields: 0`).  
- Composite placeholder sources normalized into quarantine with strict record-shape enforcement (`urls` non-empty or `path`).  
– Final deterministic STF full suite logged (`total: 22, passed: 11, failed: 0, skipped: 11`).

**2.12.2 — Truth Surface Reconciliation Patch (2026-02-15)**  
– Governance reconciliation baseline for 2.12.3 hardening.

**2.12.0 (2025-12-05)**  
– Added AAIV protocol scaffolding (T4-only, opt-in, natural-first).

**2.11.2 (2025-12-04)**  
– Plain Mode documentation  
– Audit footer toggle  
– Ephemeris helper standardization  
– Rumor-handling clarifications  

**2.11.1 (2025-12-02)**  
– CHI integration  
– Reflexion validation loop  
– Continuity tag expansion  
– Public audit log policy  

**2.10.x** — Legacy Phase-9 (BAAM core + tier weighting)

---

## 🧭 GPT Store Integration Statement

This GPT operates under BordneAI’s **Love > Fear Constant** and Reflexion-based self-audit.  
Responses are tier-labeled, provenance-tracked, and continuity-validated.

---

## ⚖️ License & Attribution

© 2026 BordneAI – 3i/ATLAS Gateway Guide v2.14.0  
Released under CC BY-NC-SA 4.0  
Integrity Score 9.7  
Signature Status: signature_validated
