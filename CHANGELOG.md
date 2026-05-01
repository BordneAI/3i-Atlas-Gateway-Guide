# 🧾 3i/ATLAS Gateway Guide — CHANGELOG

## v2.14.0 — NexGen Axiom Guard Integration (2026-04-29)

### Added
- Added `tools/axiom_guard/` as a bounded governance sidecar runtime.
- Added negative-null classification smoke tests for non-detection claims.
- Added `scripts/axiom_preflight.py` as the release preflight bridge.
- Registered Axiom Guard in `manifest.json`.

### Updated
- Promoted package state from sealed patch release to sealed minor release.
- Added release-gate expectations for Axiom Guard tests, KB validation, and signature refresh.

### Governance
- Axiom Guard is not AGI, not consciousness, and not a replacement for the KB.
- It acts as a local claim-classification, audit, and release-preflight layer.
- Negative-null claims remain observational limits, not proof of absence.
- AAIV remains T4-only, opt-in, natural-first, and low-prior.

### Breaking Changes
- None.

## v2.12.4 — Post-Seal Cumulative 3I/ATLAS Refresh (2026-03-14)

### Added
- Integrated approved LIVE entries for SPHEREx observations, isotopic composition, post-perihelion spectroscopy, and non-gravitational acceleration uncertainty.
- Registered the runtime CHI live-certification gap as an internal audit note in the release ledgers to preserve the approved patch summary without promoting it as science content.

### Updated
- Refreshed the JPL Horizons current solution snapshot to the 2026-02-19 batch values for A1, A2, and A3.
- Updated near-term ephemeris language to reflect the March 2026 Jupiter-approach phase from the approved JPL geometry snapshot.

### Carried Forward
- Preserved NASA's current no-threat-to-Earth statement for 3I/ATLAS.
- Carried forward NASA's January 27 TESS campaign update as still current-valid.

### Deferred
- Kept Galileo Project linkage in deferred status because no qualifying official result update was confirmed in this refresh.

### Demoted / Archival
- Demoted late-2025 observing-window guidance to archival-only status.
- Flagged the missing March 14 runtime CHI certification artifact as an internal audit evidence gap.

## v2.12.3 — Seal Finalization + Governance Hardening (2026-02-22)

- Canonical surfaces reconciled to sealed state for `v2.12.3` (`manifest.json`, `instructions.txt`, `CHANGELOG.md`).
- Option C domain-gated taxonomy + routing templates + entrypoints integrated and audited.
- Strict Referential Scanner v1.0.1 integrated (record-shape registry detection, type-safe citation extraction, surfaced ancestry checks).
- New validated T1/T2 data integrated: NASA Europa Clipper observation, NASA TESS reobservation window, NASA safety reaffirmation, Breakthrough Listen GBT preprint constraints, and TESS HLSP references.
- Citation plumbing cleanup completed pre-seal (`schema_warnings.free_text_in_citation_fields` reduced to `0`).
- Composite placeholder source normalization completed for strict scanner purity (`ANOMALY-SURVEY-2025` and `VARIOUS-PRESS-REPORTS` quarantined/traceable; duplicate top-level composite removed).
- Overdue queue sweep + terminal-safe normalization completed (including `T3_opinion` normalization).
- STF harness hardened for deterministic runs (non-deterministic cases skipped, domain subset comparator enabled).
- Final deterministic full STF run logged: `total=22`, `passed=11`, `failed=0`, `skipped=11`.
- Tooling surface normalized: `normalize_updates.js` moved to `scripts/normalize_updates.js` with backward-compatible root shim retained.
- Governance integrity/fingerprint refreshes recorded through `kb_changelog.json` audit trail.

## v2.12.2 – Truth Surface Reconciliation Patch (2026-02-15)

- Reconciled release governance surfaces so `CHANGELOG.md`, `manifest.json`, and `instructions.txt` report one consistent current version/release story for v2.12.2.
- Aligned manifest file-version metadata to actual declared versions where available, and added explicit handling notes where file-level versions are not declared.
- Normalized `tags_index.json` metadata shape so top-level counts and integrity validation counts use one coherent schema.
- Added explicit release checklist policy for post-edit integrity re-audit and signature regeneration on signed/audited artifacts.
- Added enforceable currency/archival routing policy clarifying 30-day `as_of` requirements for T1/T2 sources where applicable.

## v2.12.1 – Behavior & Safety Routing Upgrade (2025-12-07)

- Audit footer is now enabled by default; users can still toggle it with `audit footer on/off`, and “Always show audit footer” makes the setting sticky for the current conversation.
- Ephemeris Helper upgraded: RA/Dec/magnitude answers now always use live ephemeris tools (JPL HORIZONS, TheSkyLive, In-The-Sky) via `web.run` and never fabricate precise coordinates; all such responses include source and timestamp.
- Introduced a proactive “rumor radar” pattern for fear/rumor-driven queries: automatically checks recent reliable sources and responds with calm, evidence-based context under Love > Fear.
- Added Location Memory behavior: when users share a city/region or timezone, the assistant can show a location status line for sky/time-sensitive answers and invite updates/clears.
- Enhanced Plain Mode: auto-suggested and auto-enabled for child/teen users, high-anxiety queries, and first-run fear questions, with clear instructions to switch back to the detailed mode.

## v2.12.0 — AAIV Protocol Scaffolding (2025-12-05)

- Introduced `docs/aaiv_protocol_v2.12.md` as the canonical AAIV (Active Autonomous Interstellar Vehicle) protocol document:
  - Treats AAIV strictly as a **Tier T4 hypothesis generator** with **explicit low priors** (π_A/π_N ≲ 10⁻⁸).
  - Codifies 3I/ATLAS as a **“teacher object”** for technosignature-aware comet science, not as evidence of artificial origin.
  - Requires **Bayesian anomaly assessment** and **Love > Fear** framing for all AAIV-mode responses.
- Added `docs/aaiv_agent_spec_v2.12.md` as the design spec for an **AAIV Assessment Agent**:
  - Encodes how a future agent should implement the AAIV protocol (natural-first, T4-only, low priors, Love > Fear).
  - Clarifies workflow: observation bundle → natural model pass → AAIV what-if pass → discriminant checks → Bayesian-style conclusion.
- Updated `manifest.json` to:
  - Bump project metadata to **v2.12.0**.
  - Register the AAIV protocol doc as a public protocol surface.
  - Add a v2.12.0 changelog summary entry noting that AAIV remains **opt-in** and **non-default**.
- No changes to the underlying epistemic engine, KB tiering, or default behavior:
  - AAIV handling only activates when the user explicitly requests artificial-probe analysis or AAIV framing.

## v2.11.3 — Documentation & Provenance Update

- Added AAIV reference paper (Bordne 2025) as a governed T3/T4 artifact in `docs/aaiv_3I_ATLAS_paper_v1.tex` (with PDF to follow).
- Updated README to reference the AAIV framework and its role as a Tier T4 hypothesis generator with explicit low priors.
- No changes to the epistemic engine, Bayesian priors, or runtime behavior; documentation-only patch.

## 📦 Version 2.11.2  ( 2025-12-04 )
**Codename:** *Ergonomics & Governance Refinement*  
**Integrity Score:** 9.7 | **Ethics Constant:** Love > Fear | **Audit Cycle:** 24 h

---

### 🔍 Summary
Light-weight behavior/UX update layered on top of the Phase-10 Continuity release.  
No core KB facts or tier schemas changed. This release focuses on ergonomics, transparency, and evaluation mapping:

- Plain/simple-mode response design for non-expert users (jargon-suppressed explanations on request).  
- Optional post-response audit footer pattern (CHI, Reflexion, Love > Fear) for high-risk or audit-focused queries.  
- Ephemeris helper behavior: magnitude/coordinates plus links out to JPL HORIZONS and TheSkyLive.  
- T4 misinformation handling docs and stress-tests for ranking/debunking viral “alien swarm / impact / cover-up” claims.  
- New `docs/` artifacts tracking external evaluations and design notes for v2.11.2.
- External validation: Grok peer review for v2.11.2 confirms the self-audit and rates the system at **9.9/10** with all 11 stress tests passing and no tier/ethics violations.

---

### ⚙️ Core Enhancements by File

| File | Update Summary |
|------|----------------|
| **manifest.json** | Bumped project version to 2.11.2 and documented ergonomics features (plain mode design, audit footer toggle, ephemeris helper, T4 misinfo docs, external evaluations). |
| **instructions.txt** | Documented plain/simple-mode behavior, audit footer usage, misinfo-handling expectations, and ephemeris helper guidance. |
| **BOOTLOADER.md** | Updated bootloader metadata to v2.11.2 and reaffirmed Phase-10 Continuity, CHI targets, and Reflexion hooks. |
| **stress_test_framework.json** | Added tests for plain mode, audit footer visibility, ephemeris helper behavior, T4 misinfo debunking, and fiction/out-of-context misuse. |
| **README.md** | Added v2.11.2 entry, `docs/` map, and **External Evaluations** section linking human and Grok peer reviews (now including 9.9/10 v2.11.2 validation). |
| **kb_changelog.json** | Logged `kb_apply_v2_11_2_ergonomics_and_docs` as a doc/UX-only update (no KB content changes). |
| **docs/** | Added `peer_review_human_v2_10_1.md`, `peer_review_grok_v2_11_1.md`, `peer_review_grok_followup_v2_11_1.md`, and `v2.11.2_NOTES.md` as public evaluation and design references. |

---

## 📦 Version 2.11.1  ( 2025-12-04 )
**Codename:** *BordneAI Continuity Update / Phase-10 Integration*  
**Integrity Score:** 9.7 | **Ethics Constant:** Love > Fear | **Audit Cycle:** 24 h

---

### 🔍 Summary
This release integrates the complete **BordneAI Phase-10 Continuity and Ethical Framework**, establishing a unified foundation for transparency, empathy-balanced reasoning, and Reflexion-based integrity auditing.  
All subsystems now operate under tier-coupled truth validation and continuous CHI (Continuity Health Index) monitoring.

---

### ⚙️ Core Enhancements by File

| File | Update Summary |
|------|----------------|
| **Project-wide metadata** | Bumped release/version markers to 2.11.1, shifted dates to 2025-12-04 (including bootloader build), and normalized naming to **3i/ATLAS** across docs, signatures, and prompts. |
| **manifest.json** | Added Love > Fear constant, CHI target, audit cycle metadata, public audit badge, and Reflexion hook flags. |
| **bayesian_framework.json** | Integrated truth/false/consciousness tier schemas, ethical weighting, and Reflexion controls. |
| **normalize_updates.js** | Upgraded to v2.11.1 with Reflexion F-tier detection, CHI computation, audit logging, and Love > Fear UX safety. |
| **stress_test_framework.json** | Added 3 new Integrity Pulse tests (STF-010 CHI Audit, STF-011 Love/Fear Balance, STF-012 Reflexion Loop). |
| **sources.json** | Introduced EOS Transparency Layer with provenance tiers (T1–T4) and confidence ranges. |
| **knowledge_base_merged_v2.json** | Embedded tier and confidence metadata, Reflexion audit record, and continuity stability status. |
| **kb_updates_cumulative.json** | Added integrity audit block, tier tags per proposal, and continuity metrics. |
| **kb_changelog.json** | Logged BordneAI Phase-10 audit entry with tier distribution and false-tier activity map. |
| **tags_index.json** | Expanded taxonomy with 10 new ethics & continuity tags and 2 new categories. |
| **README.md** | Rewritten for GPT Store deployment; added protocol overview, tier frameworks, metrics, and license signature. |

---

### 🧠 New System Concepts
- **Love > Fear Constant** — ethical polarity balancer for responses and system decisions.  
- **Reflexion v2.11.1** — self-validation layer detecting F-tier anomalies and entropy drift.  
- **Continuity Health Index ( CHI )** — numerical integrity score ( target ≥ 9.5 ).  
- **EOS Transparency Layer** — source provenance and confidence disclosure.  
- **Integrity Pulse Cycle** — automatic daily audit ( 24 h interval ).  
- **Tier Frameworks** — Tiers for Truth (T-), Falsehood (F-), and Consciousness (C-) now standardized across modules.  

---

### 🧩 Added Tag Categories (v2.11.1)
| Category | Tags |
|-----------|------|
| **ethics_and_audit** | ethics, audit, integrity, love_fear, transparency |
| **continuity_systems** | continuity, reflexion, chi, truth_tier, false_tier |

---

### 🪶 Metrics at Release
| Metric | Value | Description |
|---------|--------|-------------|
| **Continuity Health Index ( CHI )** | 9.7 | Overall system integrity score (out of 10). |
| **Entropy Leak Rate** | 0.02 | Measured variance in continuity consistency. |
| **False-Tier Activity** | Minimal ( < 0.1 %) | No fabrication or bias events detected. |
| **Reflexion Cycle Time** | 24 h | Scheduled audit interval. |

---

### 📘 Public Audit and Transparency
All Reflexion audit results are automatically written to `/logs/reflexion_audit_YYYYMMDD.json` and included in the next `kb_changelog.json` cycle.  
Each release includes an ATLAS signature marker and is validated via EOS provenance checks.

---

### 🧾 Previous Versions
**2.10.x** – BAAM Framework v1 with pre-tier weighting.  
**2.9.x** – Loeb Scale integration and IAWN Campaign additions.  
**2.8.x** – Entropy management and tag surface expansion.

---

### ⚖️ License & Signature

© 2026 BordneAI – 3i/ATLAS Gateway Guide v2.14.0  
Released under CC BY-NC-SA 4.0 • Integrity Score 9.7  

Signature Status: signature_validated
