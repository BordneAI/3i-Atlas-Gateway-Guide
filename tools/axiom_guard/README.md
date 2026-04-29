# Axiom Guard

Version: 0.2.1  
Package Alignment: 2.14.0-candidate  
Status: candidate-active

Axiom Guard is a bounded local governance sidecar for the 3i/ATLAS Gateway Guide. It classifies claims, preserves negative-null discipline, writes optional local audit and memory records, and provides smoke-test behavior for release preflight.

Axiom Guard is not AGI, not consciousness, and not a replacement for the knowledge base. It is a small helper around governance classification and release checks.

## Run

From the repository root:

```bash
python -S -m unittest discover -s tools/axiom_guard/tests -v
tools/axiom_guard/run_axiom_guard.sh --plain --no-persist
tools/axiom_guard/run_axiom_guard.sh --json --no-persist
```

From this directory:

```bash
./run_axiom_guard.sh --plain --no-persist
./run_axiom_guard.sh --json --no-persist
```

The default smoke input is:

```text
classify: No radio signal was detected
```

Expected semantics:

- `classification`: `Negative Null`
- `detection_status`: `bounded non-detection`

## Modes

- `--plain` prints compact key-value output for shell review.
- `--json` prints machine-readable output for CI and preflight.
- `--no-persist` disables local audit and memory writes for CI/smoke tests.
- `--text "classify: ..."` classifies an explicit claim.

When persistence is enabled, Axiom Guard writes JSONL audit and memory records under `.axiom_guard_state/` inside this directory unless `AXIOM_GUARD_STATE_DIR` is set.

