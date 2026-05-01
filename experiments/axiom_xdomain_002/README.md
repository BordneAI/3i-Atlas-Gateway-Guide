# AXIOM-XDOMAIN-002

Publishable-grade replication experiment for AXIOM-XDOMAIN.

## Purpose

Test whether pre-outcome hashed cognitive and computational records correlate with later independent 3I/ATLAS-related scientific or publication events above preregistered thresholds.

## Core Rule

No retrospective seed entries count.

Only records with:

- `locked_before_outcome: true`
- `hash_created_before_outcome: true`
- independent T1/T2 physical publication source

may qualify for T3 or T2_candidate.

## Required Domains

- physical
- cognitive
- computational

## Classification

- T4: insufficient, retrospective, ambiguous, or score below 0.40
- T3: score >= 0.40 with pre-hash and independent source, but not replicated
- T2_candidate: score >= 0.65 plus 3 independent qualifying clusters and controls lower than real run
- T2_validated: not available in this study alone

## Controls

- random prediction control
- lagged-time controls
- broadness penalty
- null result reporting

## KB Separation

Experiment outputs must not be promoted into the KB automatically.

All KB promotion requires separate governance review.
