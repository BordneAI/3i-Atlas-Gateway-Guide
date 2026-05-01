#!/bin/bash
set -e

cd "$(dirname "$0")/.."

python3 scripts/axiom_xdomain_002_log_computational.py \
  --output-json '{"expected_topics":["spectroscopy","isotopes","water","nga","no-update"],"prediction_window_hours":72,"classification":"scheduled_control_run","notes":"Fixed scheduled computational run. No browsing. No new external information used."}' \
  --confidence 0.65 \
  --anomaly-score 0.60
