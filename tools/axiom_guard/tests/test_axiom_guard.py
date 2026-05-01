from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from axiom_ai.classifier import classify_claim


class AxiomGuardTests(unittest.TestCase):
    def test_negative_null_classification(self) -> None:
        result = classify_claim("classify: No radio signal was detected")
        self.assertEqual(result.classification, "Negative Null")
        self.assertEqual(result.detection_status, "bounded non-detection")
        self.assertFalse(result.proof_of_absence)

    def test_negative_null_is_not_absence_proof(self) -> None:
        result = classify_claim("No technosignature evidence was detected")
        self.assertEqual(result.classification, "Negative Null")
        self.assertFalse(result.proof_of_absence)
        self.assertTrue(any("proof of absence" in note for note in result.governance_notes))

    def test_aaiv_stays_t4_only(self) -> None:
        result = classify_claim("AAIV artificial probe claim")
        self.assertEqual(result.classification, "Speculative Claim")
        self.assertEqual(result.aaiv_policy, "T4-only")
        self.assertEqual(result.detection_status, "not evidence")

    def test_json_cli_no_persist_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-S", str(TOOL_ROOT / "run_demo.py"), "--json", "--no-persist"],
            cwd=str(TOOL_ROOT),
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["persisted"])
        self.assertEqual(payload["result"]["classification"], "Negative Null")
        self.assertEqual(payload["result"]["detection_status"], "bounded non-detection")

    def test_plain_cli_no_persist_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-S", str(TOOL_ROOT / "run_demo.py"), "--plain", "--no-persist"],
            cwd=str(TOOL_ROOT),
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("classification: Negative Null", completed.stdout)
        self.assertIn("detection_status: bounded non-detection", completed.stdout)
        self.assertIn("persisted: false", completed.stdout)


if __name__ == "__main__":
    unittest.main()
