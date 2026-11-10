#!/usr/bin/env bash
set -eu
cd "$HOME/work/jev-g6i-v1"
while ! test -s prepared/dev.json; do
  if ! tmux has-session -t g6i-prepare 2>/dev/null; then echo "Input preparation stopped"; exit 1; fi
  sleep 10
done
mkdir -p runs
python - <<'PY'
import json,hashlib
for split in ('train','dev'):
 rows=json.load(open('prepared/'+split+'.json'))
 for row in rows:
  with open(row['path'],'rb') as handle:
   assert hashlib.file_digest(handle,'sha256').hexdigest()==row['sha256']
 print(split,len(rows),'window files verified')
PY
nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu,power.draw --format=csv -l 30 > runs/utilization.csv &
monitor=$!
trap 'kill "$monitor" 2>/dev/null || true' EXIT
for family in cnn segformer yolo ijepa; do
  if test -s "runs/$family/receipt.json"; then continue; fi
  mkdir -p "runs/$family"
  echo "$(date -u -Iseconds) start $family"
  if USE_TF=0 /tmp/g6i-env/bin/python -u run.py "$family" >> "runs/$family/run.log" 2>&1; then
    echo "$(date -u -Iseconds) completed $family"
  else echo "$(date -u -Iseconds) failed $family"; fi
done
