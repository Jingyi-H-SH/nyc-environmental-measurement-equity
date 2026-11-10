#!/usr/bin/env bash
# Run from any location. Only frozen population metadata and archived input QA are read.
set -euo pipefail
cd "$(dirname "$0")/../.."
P=.venv/bin/python
for stage in audit summarize frozen_sensitivity report test_qualification; do
  if [[ "$stage" == summarize ]]; then "$P" experiments/g6h/package_receipts.py unpack; fi
  "$P" "experiments/g6h/$stage.py"
done
