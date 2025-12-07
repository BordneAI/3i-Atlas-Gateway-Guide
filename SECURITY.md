# Security Policy – 3i/ATLAS Gateway Guide

_Last updated: 2025-12-07_

Thank you for taking the time to help keep the 3i/ATLAS Gateway Guide safe, honest, and reliable.

This repository contains **configuration, documentation, and knowledge bases** for the 3i/ATLAS Gateway Guide GPT (epistemic governance system for 3I/ATLAS / C/2025 N1), not a traditional executable application. Security issues here are primarily about **misuse, misconfiguration, and misinformation**, not local code execution bugs.

---

## 📌 Scope

Please treat the following as “in scope” for security reports:

- **Prompt / configuration vulnerabilities**, including:
  - Prompt-injection patterns that reliably bypass:
    - Love > Fear safeguards  
    - tiered evidence rules (T1–T4)  
    - AAIV/BAAM guardrails (e.g., forcing “AAIV is likely” or similar claims).
  - Ways to cause the system to:
    - fabricate precise ephemeris (RA/Dec, magnitude) instead of using tools  
    - present speculation (T4) as fact (T1/T2).

- **Misinformation & safety failures**, including:
  - Reproducible paths that:
    - escalate fear rather than de-escalate it (e.g., “impact,” “doomsday,” “invasion”),  
    - undermine mental-health safeguards (e.g., ignoring Plain Mode on child/anxiety queries),  
    - bypass rumor radar or crisis-referral behavior described in the docs.

- **Integrity / supply-chain issues**, including:
  - Unauthorized or malicious changes to:
    - `instructions.txt`  
    - knowledge base JSON files  
    - AAIV/BAAM protocol docs  
    - GitHub Actions / CI workflows that enforce governance.
  - Confusion between official vs. malicious forks presented as “the” 3i/ATLAS Gateway.

Out of scope (for this repo):

- Vulnerabilities in **OpenAI, GitHub, or other platform infrastructure**.  
  Please report those through the relevant vendor’s official channels.
- Personal account security (your own device, browser, OS, etc.).

---

## 📨 How to Report a Security Issue

If you believe you’ve found a security-relevant issue in this project, please use **one** of the following:

1. **Preferred:**  
   Open a **private security report** via GitHub (Security → “Report a vulnerability”), if available for your account.

2. **Alternative:**  
   Send an email to:  
   `security@bordne.com`  
   (If this address bounces, please open a GitHub Issue with the label `security` and avoid including sensitive details.)

When reporting, please include:

- A clear description of the issue.  
- Steps to reproduce (exact prompts, context, and screenshots if relevant).  
- The expected vs. actual behavior.  
- Any thoughts on potential impact.

Please **do not** publicly post detailed exploits or chains that can be easily weaponized before we’ve had a chance to review and respond.

---

## ⏱ Response & Disclosure Expectations

- We aim to **acknowledge** new security reports within **7 days**.
- We will prioritize:
  - issues that affect public safety messaging (e.g., false impact risk, fear amplification),
  - issues involving minors or mental-health-sensitive users,
  - configuration leaks that could meaningfully degrade governance.

If a vulnerability is confirmed, we will:

1. Work on a fix or mitigation as soon as reasonably possible.  
2. Update documentation and/or configuration to prevent recurrence.  
3. Where appropriate, publish a short, public summary of:
   - the issue (at a high level),
   - the fix,
   - any user-facing implications.

We respect responsible disclosure and ask that you give us a reasonable window to patch before broad public discussion.

---

## 🙏 Non-Security Issues

For feature requests, documentation improvements, or general questions (including astronomy, CE-5 bridge, AAIV/BAAM usage, etc.), please use:

- **GitHub Issues** (label: `enhancement`, `docs`, or `question`), or  
- GitHub **Discussions** (if enabled).

These help keep security reporting focused and efficient.

---

## ⚖️ Disclaimer

The 3i/ATLAS Gateway Guide is a **governance and outreach system**, not a guarantee of truth or safety.  
We strive for:

- accurate, tiered sourcing,  
- Love > Fear tone,  
- strong refusal and de-escalation behavior.

However, no system is perfect.  
Your reports and contributions are part of how we keep this work aligned, safe, and worthy of public trust.

Thank you for helping safeguard this project and its users.
