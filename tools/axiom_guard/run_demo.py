#!/usr/bin/env python3
"""Run the Axiom Guard CLI with isolated-startup friendly imports."""

from __future__ import annotations

import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from axiom_ai.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

