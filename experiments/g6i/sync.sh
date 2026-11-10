#!/usr/bin/env bash
# Copy only compact development evidence. Per-window masks and weights stay on the persistent Featurize mount.
set -eu
cd "$(dirname "$0")/../.."
mkdir -p manifests/g6i/run
rsync -rt --exclude='predictions/' --include='*/' --include='*.log' --include='config.json' --include='receipt.json' --include='sha256.json' --include='tract_confusion.json' --include='tract_shares.json' --include='matched_dense_counts.json' --include='utilization.csv' --exclude='*' --prune-empty-dirs jev-g6-featurize:work/jev-g6i-v1/runs/ manifests/g6i/run/runs/
rsync -rt --include='*.log' --include='*environment.txt' --include='*.sha' --include='qwen_official_revision.json' --exclude='*' jev-g6-featurize:work/jev-g6i-v1/ manifests/g6i/run/
.venv/bin/python experiments/g6i/measure.py manifests/g6i/run/runs
