"""Optional local persistence for Axiom Guard audit and memory records."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Mapping


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LocalLedger:
    def __init__(self, base_dir: str | None = None, persist: bool = True) -> None:
        default_dir = Path(__file__).resolve().parents[1] / ".axiom_guard_state"
        self.base_dir = Path(base_dir or os.environ.get("AXIOM_GUARD_STATE_DIR", str(default_dir)))
        self.persist = persist

    def record(self, result: Mapping[str, object]) -> Mapping[str, object]:
        entry = {"recorded_at": utc_now(), "result": dict(result)}
        if not self.persist:
            return {**entry, "persisted": False}

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._append_jsonl(self.base_dir / "audit_log.jsonl", entry)
        self._append_jsonl(self.base_dir / "memory.jsonl", self._memory_entry(entry))
        return {**entry, "persisted": True}

    @staticmethod
    def _append_jsonl(path: Path, entry: Mapping[str, object]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    @staticmethod
    def _memory_entry(entry: Mapping[str, object]) -> Mapping[str, object]:
        result = entry.get("result", {})
        if not isinstance(result, Mapping):
            result = {}
        return {
            "recorded_at": entry.get("recorded_at"),
            "claim": result.get("claim"),
            "classification": result.get("classification"),
            "detection_status": result.get("detection_status"),
        }

