#!/usr/bin/env bash
# Collect this experiment exactly once after both model queues exit.
set -eu
cd "$(dirname "$0")/../.."
ssh -o ServerAliveInterval=25 jev-g6-featurize 'while tmux has-session -t g6i-dense 2>/dev/null || tmux has-session -t g6i-vlm 2>/dev/null; do sleep 45; done
cd ~/work/jev-g6i-v1
if test -s runs/qwen/receipt.json && ! test -s runs/qwen/tract_shares.json; then python qwen_reduce.py; fi'
bash experiments/g6i/collect.sh
.venv/bin/python experiments/g6i/test_measure.py
