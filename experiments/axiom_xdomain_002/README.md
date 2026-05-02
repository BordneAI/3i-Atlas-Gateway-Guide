# AXIOM-XDOMAIN-002

Publishable-grade preregistered replication experiment for AXIOM-XDOMAIN.

## Current Status

AXIOM-XDOMAIN-002 is active as a preregistered, time-observable experiment.

Current state:

- Experiment execution is active.
- Computational cadence is running.
- Cognitive prediction records exist.
- Computational baseline records exist.
- Event ingestion tooling is implemented and fixture-tested.
- Event ledger validation passes.
- Non-scoring adjudication bridge is implemented.
- Physical-event fixture adjudication test passes.
- Cadence health check is implemented and passing.
- Interim report generation is implemented.
- No real physical/publication event has been ingested yet.
- No physical matching has been performed.
- No signal conclusion can be drawn yet.

Current interpretation:

Baseline-only. No physical events have been ingested, no physical matching has been performed, and no signal conclusion can be drawn yet.

---

## Purpose

Test whether pre-outcome hashed cognitive and computational records correlate with later independent 3I/ATLAS-related scientific or publication events above preregistered thresholds.

The experiment is designed to preserve:

- preregistration integrity
- prediction/outcome independence
- append-only evidence handling
- null and exclusion visibility
- separation between experimental outputs and KB facts

---

## Core Rule

No retrospective seed entries count.

Only records with:

- `locked_before_outcome: true`
- `hash_created_before_outcome: true`
- independent physical/publication source
- no prediction-coupled event ingestion
- preserved null/exclusion accounting

may qualify for T3 or T2_candidate review.

T2_candidate requires independent qualifying clusters and cannot be established by this experiment’s scaffolding alone.

---

## Required Domains

AXIOM-XDOMAIN-002 tracks three domains:

- physical
- cognitive
- computational

Current live event ledger state:

- cognitive records: 5
- computational records: 10
- physical records: 0

---

## Classification

- T4: insufficient, retrospective, ambiguous, contaminated, or score below `0.40`
- T3: score `>= 0.40` with pre-hash and independent source, but not replicated
- T2_candidate: score `>= 0.65` plus 3 independent qualifying clusters and controls lower than real run
- T2_validated: not available in this study alone

Current status:

- Signal conclusion: none
- T2_candidate assessment: blocked

---

## Controls

Controls include:

- random prediction control
- lagged-time controls
- broadness penalty
- contamination penalty
- null result reporting
- exclusion preservation
- scheduled computational baseline

Current scoring snapshot:

- scoring records: 10
- scored records: 8
- scoring exclusions: 2
- total score: 0.0
- mean score: 0.0

This score is baseline/null behavior and does not indicate positive or negative anomaly evidence.

---

## Phase Map

### Phase 1 — Foundation / Lock

Status: Done

Related issues:

- #38
- #39
- #42
- #59

### Phase 2 — Baseline Data Collection

Status: Operational / in review

Related issues:

- #44
- #54
- #57
- #58

### Phase 3 — Dataset Integrity & Separation

Status: In progress

Related issues:

- #43
- #45
- #46
- #49

### Phase 4 — Event Ingestion

Status: In progress / waiting for first real independent source

Related issues:

- #40
- #41
- #60

### Phase 5 — Outcome Adjudication

Status: Bridge implemented / matching pending

Related issues:

- #52
- #61

### Phase 6 — Scoring / Reporting

Status: Partially implemented / reporting in review

Related issues:

- #53
- #55
- #56
- #62

### Phase 7 — Evaluation / Promotion Review

Status: Blocked

Related issues:

- #47
- #48

Important distinction:

- #48 execution is active.
- #48 final completion/evaluation is blocked.

---

## Directory Structure

Primary experiment directory:

- `experiments/axiom_xdomain_002/`

Important files:

- `LOCK.json`
- `preregistration.json`
- `scoring_model.lock.json`
- `cross_domain_events.json`
- `null_results.json`
- `normalized_computational_events.json`
- `scores.json`
- `adjudication_draft.json`
- `SOURCE_ELIGIBILITY.md`
- `reports/summary.json`
- `reports/summary.md`

Raw records:

- `raw/cognitive/`
- `raw/computational/`

Logs:

- `logs/monitoring_log.jsonl`

Scripts:

- `scripts/axiom_xdomain_002_add_physical.py`
- `scripts/axiom_xdomain_002_validate_events.py`
- `scripts/axiom_xdomain_002_test_physical_adjudication_fixture.py`
- `scripts/axiom_xdomain_002_adjudicate.py`
- `scripts/axiom_xdomain_002_healthcheck.py`
- `scripts/axiom_xdomain_002_normalize_computational.py`
- `scripts/axiom_xdomain_002_score.py`
- `scripts/axiom_xdomain_002_report.py`

---

## Integrity Rules

Do not:

- modify raw prediction files
- modify raw computational output files
- regenerate hashes for old records
- delete nulls, exclusions, or ambiguous outcomes
- append fake physical events to the live ledger
- ingest physical events based on prediction matching
- promote experimental results into the KB
- infer signal before physical event ingestion and adjudication

Do:

- preserve raw records
- use derived files for normalization, scoring, adjudication, and reports
- keep nulls and exclusions visible
- use source eligibility before ingesting physical events
- validate event ledger after ingestion
- run health check after scheduled cadence outputs
- document deviations explicitly

---

## Computational Cadence

Scheduled computational outputs are stored under:

- `experiments/axiom_xdomain_002/raw/computational/`

The cadence must:

- use no browsing
- use no live external data
- use the fixed AXIOM-XDOMAIN-002 computational prompt
- preserve raw computational outputs
- avoid modifying locked experiment files

Check current state:

    python3 scripts/axiom_xdomain_002_healthcheck.py --json

---

## Normalization and Scoring

Normalize computational records:

    python3 scripts/axiom_xdomain_002_normalize_computational.py

Run scoring:

    python3 scripts/axiom_xdomain_002_score.py

Inspect scores:

    cat experiments/axiom_xdomain_002/scores.json

Current scoring behavior:

- fallback/generated recovery outputs are excluded
- valid no-update computational outputs are retained as null baseline records
- current total score is baseline/null behavior
- physical event matching is not yet integrated into scoring

---

## Physical / Cross-Domain Event Ingestion

Physical events must be independently sourced.

Before ingesting any physical event, read:

- `experiments/axiom_xdomain_002/SOURCE_ELIGIBILITY.md`

Physical event ingestion must not reference:

- prediction IDs
- prediction text
- desired score
- desired outcome
- candidate hit/miss status

Dry-run example:

    python3 scripts/axiom_xdomain_002_add_physical.py --timestamp-utc 2026-05-02T00:00:00Z --source-tier T3 --confidence 0.50 --event-type test-event --topic-tags test --description "Dry-run only; not appended." --source-reference "dry-run-local-test" --contamination-risk 0.0 --dry-run

Validate event ledger:

    python3 scripts/axiom_xdomain_002_validate_events.py --json

Do not append test events to the live ledger.

For fixture-safe testing, use:

    python3 scripts/axiom_xdomain_002_test_physical_adjudication_fixture.py

---

## Outcome Adjudication

Generate the non-scoring adjudication draft:

    python3 scripts/axiom_xdomain_002_adjudicate.py

Output:

- `experiments/axiom_xdomain_002/adjudication_draft.json`

The current bridge:

- reads cognitive and computational records
- computes outcome windows
- applies logged exclusions
- preserves raw records
- does not perform physical matching
- does not perform scoring

Physical matching remains pending until eligible real physical events are ingested or a fixture-only matching test is intentionally added.

---

## Health Check

Run:

    python3 scripts/axiom_xdomain_002_healthcheck.py --json

The health check verifies:

- latest computational output exists
- latest output is fresh
- event ledger validates
- latest output appears in `cross_domain_events.json`
- latest output appears in `scores.json`
- adjudication draft exists
- adjudication still reports no scoring
- adjudication still reports no physical matching

If health check warns about stale derived files, refresh:

    python3 scripts/axiom_xdomain_002_normalize_computational.py
    python3 scripts/axiom_xdomain_002_score.py
    python3 scripts/axiom_xdomain_002_adjudicate.py
    python3 scripts/axiom_xdomain_002_report.py

Then commit the new scheduled cadence output and refreshed derived artifacts.

---

## Reporting

Generate interim report:

    python3 scripts/axiom_xdomain_002_report.py

Outputs:

- `experiments/axiom_xdomain_002/reports/summary.json`
- `experiments/axiom_xdomain_002/reports/summary.md`

The interim report must clearly state:

- baseline-only
- no physical events ingested
- no physical matching performed
- no signal conclusion yet
- T2_candidate assessment blocked

---

## KB Separation

Experiment outputs must not be promoted into the KB automatically.

All KB promotion requires separate governance review.

AXIOM-XDOMAIN outputs are experimental by default:

- experimental
- preregistered
- T3 screening
- not authoritative
- not promotable without review

Promotion requires:

- event ingestion complete
- adjudication complete
- final scoring complete
- nulls and exclusions included
- contamination reviewed
- replication requirements satisfied
- manual governance approval

---

## T2_candidate Status

T2_candidate review is blocked.

Current blocking conditions:

- no real physical events ingested
- no physical matching performed
- no final hit/miss adjudication
- no final scoring result
- no final evaluation report

T2_candidate is not a truth claim. It is only a future review status if locked criteria are satisfied.

---

## Safe Operating Procedure

After each scheduled cadence run:

1. Inspect or run health check.
2. If needed, normalize computational records.
3. Run scoring.
4. Run adjudication draft.
5. Run report generator.
6. Commit new raw computational output and derived artifacts.
7. Do not alter raw history.

Recommended command sequence:

    python3 scripts/axiom_xdomain_002_healthcheck.py --json
    python3 scripts/axiom_xdomain_002_normalize_computational.py
    python3 scripts/axiom_xdomain_002_score.py
    python3 scripts/axiom_xdomain_002_adjudicate.py
    python3 scripts/axiom_xdomain_002_report.py
    git status

Only commit after reviewing the diff.

---

## Current Limitations

- The live ledger currently has no real physical/publication events.
- Physical event matching is not implemented for live scoring.
- Final hit/miss adjudication is not complete.
- Current score is baseline/null behavior.
- No positive or negative anomaly conclusion can be drawn.
- T2_candidate review is blocked.

---

## Summary

AXIOM-XDOMAIN-002 is operational as a preregistered, time-observable baseline and audit pipeline.

It is not yet a completed signal evaluation.

The next scientific milestone is the ingestion of a real independent physical/publication event that satisfies `SOURCE_ELIGIBILITY.md`, followed by window-aware and topic-aware adjudication.
