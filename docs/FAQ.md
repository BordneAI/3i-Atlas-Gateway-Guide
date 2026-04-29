# FAQ — v2.12.4
**Version:** 2.12.4
**Package Alignment:** 2.12.4

This FAQ is a public-facing overview for users of the 3i/ATLAS Gateway Guide. It is explanatory rather than canonical; if any conflict appears, `manifest.json`, `instructions.txt`, and `CHANGELOG.md` govern.

## What is 3i/ATLAS?

3i/ATLAS refers to the interstellar object designated C/2025 N1. In this project, the Gateway Guide is a structured knowledge and response system built to discuss 3I/ATLAS using provenance-aware, rumor-resistant, and uncertainty-labeled answers.

In plain terms: it is a guide for talking about the object responsibly, not just a pile of claims about it.

## Is the comet dangerous?

The guide is built to answer safety questions conservatively and with current authoritative sources. It is designed not to guess, dramatize, or turn uncertainty into panic.

If a user asks whether 3I/ATLAS is dangerous, the intended behavior is:

- check current evidence
- rely on stronger sources first
- say clearly when there is no evidence of danger
- avoid fear-based exaggeration

For time-sensitive safety questions, the system's policy is to prefer live verification over stale memory.

## How does the GPT avoid fear-mongering and misinformation?

It uses several safeguards together:

- provenance tiers that separate stronger evidence from weaker material
- Rumor Radar for scary or viral claims
- Reflexion self-audit for fabrication, bias, and escalation risks
- Love > Fear tone rules that prioritize calm, factual communication
- explicit refusal to present speculation as established fact

The result is meant to be reassuring without being dismissive and careful without being vague.

## What does "Love > Fear" mean in practice?

It means the guide should respond in ways that reduce unnecessary panic while staying honest about evidence and uncertainty.

In practice, that includes:

- using calm wording
- not sensationalizing rumors
- giving reality-based reassurance when evidence supports it
- staying respectful when users are scared
- protecting curiosity without feeding panic

It does not mean "tell people everything is fine no matter what." It means truth should be delivered in a grounded, humane way.

## How is AAIV handled?

AAIV, or Active Autonomous Interstellar Vehicle, is treated as speculation only.

The project's rules are explicit:

- AAIV is Tier T4 only
- natural explanations are preferred first
- AAIV is a what-if framework, not a default conclusion
- the system must not claim that 3I/ATLAS is probably or definitely artificial

This allows discussion of speculative ideas without blurring the line between hypothesis and evidence.

## Why does the guide talk about tiers and provenance?

Because not all claims are equally strong.

The repo uses tiering to help separate:

- direct empirical or agency-backed material
- reasonable interpretation
- community discussion
- explicit speculation

That structure makes it easier to answer clearly while still showing what is known, what is inferred, and what remains uncertain.

## Why might the guide answer differently for anxious users or kids?

The system includes Plain Mode, which simplifies language and reduces jargon when a user is young, distressed, or asking a fear-heavy first question.

Plain Mode does not lower evidence standards. It only changes presentation so the answer is easier to understand and less likely to intensify fear.

## Where should I look if I want more detail?

If you want deeper repo context:

- `README.md` for the project overview
- `docs/GOVERNANCE_OVERVIEW.md` for the governance model
- `docs/aaiv_protocol_v2.12.md` and `docs/aaiv_agent_spec_v2.12.md` for the AAIV speculative framework and its guardrails

For release truth, the authoritative surfaces remain:

- `manifest.json`
- `instructions.txt`
- `CHANGELOG.md`
