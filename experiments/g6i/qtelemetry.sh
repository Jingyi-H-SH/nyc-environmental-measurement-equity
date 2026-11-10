#!/usr/bin/env bash
# Resource observations only for this frozen inference process.
set -eu
cd "$HOME/work/jev-g6i-v1"
while tmux has-session -t g6i-vlm 2>/dev/null; do
  if pgrep -f '^/tmp/g6i-vlm/bin/python -u qwen.py$' >/dev/null; then
    mkdir -p runs/qwen
    nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu,power.draw --format=csv,noheader >> runs/qwen/utilization.csv
  fi
  sleep 30
done
