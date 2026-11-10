#!/usr/bin/env bash
set -eu
cd "$HOME/work/jev-g6j-v1"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,power.draw --format=csv,noheader,nounits -l 15 >> device.csv &
sampler=$!
trap 'kill "$sampler" 2>/dev/null || true' EXIT
date -u '+start %FT%TZ'
USE_TF=0 /tmp/g6i-env/bin/python -u infer.py
date -u '+completed %FT%TZ'
