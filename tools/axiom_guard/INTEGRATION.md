# Axiom Guard Integration

Version: 0.2.1  
Package Alignment: 2.14.0-candidate

## Role

Axiom Guard is mounted as a bounded governance sidecar for v2.14.0-candidate. It sits beside the existing KB and release validators; it does not replace either one.

The sidecar provides:

- claim classification for release smoke checks
- negative-null handling for non-detection statements
- optional local audit logging
- optional memory recall records
- a JSON surface consumed by `scripts/axiom_preflight.py`

## Boundaries

- Axiom Guard is not AGI.
- Axiom Guard is not consciousness.
- Axiom Guard is not a KB authority.
- Axiom Guard must not promote AAIV above T4.
- Axiom Guard treats negative-null claims as bounded non-detection, not proof of absence.

## Release Preflight Bridge

`scripts/axiom_preflight.py` calls the sidecar in JSON mode with `--no-persist` and confirms the smoke semantics:

```bash
tools/axiom_guard/run_axiom_guard.sh --json --no-persist
```

The bridge also runs the sidecar unit tests with isolated Python startup:

```bash
python -S -m unittest discover -s tools/axiom_guard/tests -v
```

If a local environment does not provide `python`, use `python3 -S` for the same startup behavior.

