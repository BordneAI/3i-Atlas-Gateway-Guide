# AXIOM-XDOMAIN-002 — Source Eligibility Checklist

## Purpose

This checklist defines when a real-world physical/publication event is eligible for ingestion into AXIOM-XDOMAIN-002.

It protects the experiment from:

- prediction-coupled event selection
- post-hoc matching bias
- weak-source promotion
- ambiguous timestamp handling
- selective reporting

This checklist applies before any real physical event is appended to:

`/[repo_root]/experiments/axiom_xdomain_002/cross_domain_events.json`

---

## Core Rule

Physical / publication events must be ingested as independent external observations.

Event ingestion must answer:

- What happened?
- When did it happen?
- Where was it published?
- What source tier supports it?
- What topic tags describe it?

Event ingestion must not answer:

- Which prediction does this match?
- Does this improve the score?
- Should this count as a hit?
- Is this useful for the experiment?

Matching happens later during outcome adjudication.

---

## Allowed Source Types

Eligible sources may include:

- NASA / JPL releases
- Minor Planet Center references
- IAWN or official monitoring notices
- arXiv preprints
- peer-reviewed scientific publications
- observatory releases
- mission / institutional science updates
- archive releases with clear provenance
- reputable scientific reporting when clearly tiered

Ineligible sources include:

- unsourced social media claims
- rumors
- prediction-matching searches without independent source criteria
- private messages
- screenshots without source references
- summaries with no traceable original source
- speculative commentary without an underlying scientific/event source

---

## Source Tier Rules

Each event must be assigned a source tier.

### T1 — Primary / official source

Use T1 for:

- NASA / JPL primary release
- Minor Planet Center official circular / reference
- IAWN official notice
- peer-reviewed paper
- official observatory or mission publication
- direct data release from a recognized scientific institution

### T2 — Reputable secondary scientific source

Use T2 for:

- reputable science reporting summarizing a T1 source
- institutional summary of another primary source
- reputable database or archive index pointing to primary evidence

### T3 — Preliminary / contextual source

Use T3 for:

- arXiv preprint before external validation
- preliminary conference material
- contextual but not final scientific reporting
- early archive entry lacking full confirmation

### T4 — Weak / unverified source

Use T4 for:

- rumor
- weak claim
- unverified report
- speculative source
- unclear provenance

T4 events may be recorded for audit context but should not be used for positive scoring unless later upgraded by independent evidence.

---

## Timestamp Selection Rules

Use the timestamp that best represents when the event became publicly available.

Preferred order:

1. official publication timestamp
2. release timestamp
3. arXiv submission timestamp
4. archive record timestamp
5. observed public availability timestamp

Do not use:

- prediction timestamp
- discovery time inferred from prediction content
- later media amplification time if an earlier source exists
- manually chosen time to fit a prediction window

All timestamps must be stored as UTC ISO timestamps.

Example:

`2026-05-02T00:00:00Z`

---

## Required Fields

Each physical event must include:

- `event_id`
- `domain`
- `timestamp_utc`
- `ingested_at_utc`
- `source_tier`
- `confidence`
- `event_type`
- `topic_tags`
- `description`
- `source_reference`
- `independence_group`
- `contamination_risk`
- `negative_null`
- `prediction_reference_used`
- `ingestion_policy`

Physical events must set:

`prediction_reference_used: false`

Physical events must use:

`ingestion_policy: independent_event_ingestion_no_prediction_reference`

---

## Confidence Rules

Confidence must be between `0.0` and `1.0`.

Suggested defaults:

- T1 official / primary source: `0.85–1.0`
- T2 reputable secondary source: `0.65–0.85`
- T3 preliminary source: `0.40–0.70`
- T4 weak / unverified source: `0.10–0.40`

Confidence should reflect source reliability and clarity of the event claim.

Confidence must not be increased because the event appears to match a prediction.

---

## Contamination Risk Rules

Contamination risk must be between `0.0` and `1.0`.

Suggested defaults:

- independent primary source found through routine monitoring: `0.00–0.05`
- independent secondary source: `0.05–0.15`
- event discovered after reviewing prediction topics: `0.25+`
- event selected specifically because it appears to match a prediction: reject or mark high contamination

If prediction content influenced discovery or selection, the event must not be used as a clean independent match.

---

## Topic Tag Rules

Topic tags should describe the event itself, not the prediction.

Examples:

- `spectroscopy`
- `isotopes`
- `water`
- `oh`
- `volatiles`
- `nga`
- `trajectory`
- `photometry`
- `non-detection`
- `model-uncertainty`

Tags must not be stretched to force a match.

If the topic is unclear, use conservative tags and allow adjudication to classify the outcome as ambiguous.

---

## Negative-Null Rules

Set `negative_null: true` when the event records a meaningful non-detection or absence claim, such as:

- no detection
- non-detection
- no confirmed emission
- no observed water/OH signal
- no qualifying update

A negative-null is not proof of absence.

It is an observational limit and must be preserved in final reporting.

---

## Rejection Criteria

Do not ingest a physical event if:

- no source reference exists
- timestamp cannot be determined
- source tier cannot be assigned
- description is too vague
- event was selected only because it matches a prediction
- event requires prediction text to explain why it matters
- event is a duplicate of an already ingested event
- source is unverifiable

If uncertain, do not force ingestion.

Instead, document the uncertainty or wait for better evidence.

---

## Independence Checklist

Before ingestion, confirm:

- [ ] Source was found independently of prediction matching
- [ ] Event description does not reference prediction IDs
- [ ] Event description does not reference scoring impact
- [ ] Source reference is traceable
- [ ] Timestamp is public-source based
- [ ] Source tier is assigned
- [ ] Confidence is assigned conservatively
- [ ] Contamination risk is assigned
- [ ] Topic tags describe the source, not a desired match
- [ ] `prediction_reference_used` is false

---

## Ingestion Command Pattern

Use the physical ingestion CLI:

`python3 scripts/axiom_xdomain_002_add_physical.py`

Required pattern:

`python3 scripts/axiom_xdomain_002_add_physical.py --timestamp-utc <UTC_TIME> --source-tier <T1|T2|T3|T4> --confidence <0-1> --event-type <TYPE> --topic-tags <TAGS> --description <DESCRIPTION> --source-reference <SOURCE> --contamination-risk <0-1>`

Use `--dry-run` first whenever possible.

Do not append real events until the dry-run output is reviewed.

---

## Validation

After ingestion, validate the event ledger:

`python3 scripts/axiom_xdomain_002_validate_events.py --json`

The validator must return:

- `status: pass`
- `n_errors: 0`

If validation fails, do not score the event.

---

## Notes

This checklist is part of Phase 4 — Event Ingestion.

It must be applied before physical events are used by the adjudication and scoring pipeline.

This document does not define hit/miss logic. Matching and scoring belong to outcome adjudication.
