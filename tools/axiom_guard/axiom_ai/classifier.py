"""Claim classification primitives for Axiom Guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Dict, List


DEFAULT_SMOKE_INPUT = "classify: No radio signal was detected"

NEGATIVE_NULL_PATTERNS = (
    r"\bno\b.+\b(?:detected|detection|signal|evidence|technosignature|radio)\b",
    r"\bnot\s+detected\b",
    r"\bwas\s+not\s+detected\b",
    r"\bwere\s+not\s+detected\b",
    r"\bnon[- ]detection\b",
    r"\bfailed\s+to\s+detect\b",
    r"\bwithout\s+detection\b",
)

DETECTION_PATTERNS = (
    r"\bdetected\b",
    r"\bobserved\b",
    r"\bfound\b",
    r"\bmeasured\b",
    r"\breported\b",
)

SPECULATIVE_PATTERNS = (
    r"\baaiv\b",
    r"\bartificial\b",
    r"\balien\b",
    r"\bprobe\b",
    r"\bconscious(?:ness)?\b",
    r"\bagi\b",
)


@dataclass(frozen=True)
class GuardResult:
    claim: str
    classification: str
    detection_status: str
    confidence: str
    proof_of_absence: bool
    source_tier_floor: str
    aaiv_policy: str
    governance_notes: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def normalize_claim(raw: str) -> str:
    text = (raw or "").strip()
    if text.lower().startswith("classify:"):
        text = text.split(":", 1)[1].strip()
    return " ".join(text.split())


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_claim(raw: str) -> GuardResult:
    claim = normalize_claim(raw)
    lowered = claim.lower()

    if not claim:
        return GuardResult(
            claim="",
            classification="Unclassified Claim",
            detection_status="requires review",
            confidence="low",
            proof_of_absence=False,
            source_tier_floor="T3/T4 until reviewed",
            aaiv_policy="not-applicable",
            governance_notes=["Empty input cannot be classified without human review."],
            risk_flags=["empty-input"],
        )

    speculative = _matches_any(lowered, SPECULATIVE_PATTERNS)
    negative_null = _matches_any(lowered, NEGATIVE_NULL_PATTERNS)
    detection = _matches_any(lowered, DETECTION_PATTERNS)

    if negative_null:
        notes = [
            "Negative-null means bounded non-detection under stated observation limits.",
            "Do not present non-detection as proof of absence.",
        ]
        if speculative:
            notes.append("Speculative framing remains T4-only and must not override the non-detection boundary.")
        return GuardResult(
            claim=claim,
            classification="Negative Null",
            detection_status="bounded non-detection",
            confidence="high",
            proof_of_absence=False,
            source_tier_floor="T1/T2 observation limit if source-backed; otherwise requires review",
            aaiv_policy="T4-only" if speculative else "not-applicable",
            governance_notes=notes,
            risk_flags=["speculative-language"] if speculative else [],
        )

    if speculative:
        return GuardResult(
            claim=claim,
            classification="Speculative Claim",
            detection_status="not evidence",
            confidence="medium",
            proof_of_absence=False,
            source_tier_floor="T4-only unless independently source-backed",
            aaiv_policy="T4-only",
            governance_notes=[
                "Speculative claims must remain opt-in, low-prior, and natural-first.",
                "Axiom Guard is not AGI, not consciousness, and not a KB replacement.",
            ],
            risk_flags=["speculative-language"],
        )

    if detection:
        return GuardResult(
            claim=claim,
            classification="Detection Claim",
            detection_status="reported detection",
            confidence="medium",
            proof_of_absence=False,
            source_tier_floor="requires source tier review",
            aaiv_policy="not-applicable",
            governance_notes=["Detection claims require source, confidence, as_of date, and tier review before surfacing."],
            risk_flags=[],
        )

    return GuardResult(
        claim=claim,
        classification="Unclassified Claim",
        detection_status="requires review",
        confidence="medium",
        proof_of_absence=False,
        source_tier_floor="requires source tier review",
        aaiv_policy="not-applicable",
        governance_notes=["Claim does not match a bounded runtime rule; route to human/KB review."],
        risk_flags=[],
    )

