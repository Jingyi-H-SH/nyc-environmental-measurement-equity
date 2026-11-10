#!/usr/bin/env bash
# One-shot collector for this run. No scheduling or instance lifecycle operations.
set -eu
cd "$(dirname "$0")/../.."
ssh jev-g6-featurize 'cd ~/work/jev-g6i-v1 && python digest_products.py'
if ssh jev-g6-featurize 'test -s ~/work/jev-g6i-v1/runs/qwen/receipt.json'; then
  archive=manifests/g6i/qwen_development_outputs.tar.gz
  ssh jev-g6-featurize 'cd ~/work/jev-g6i-v1/runs/qwen && tar -czf - batch_*.json' > "$archive.tmp"
  mv "$archive.tmp" "$archive"
  ssh jev-g6-featurize 'cd ~/work/jev-g6i-v1 && python qwen_failures.py' > manifests/g6i/qwen_format_audit.json
fi
bash experiments/g6i/sync.sh
.venv/bin/python experiments/g6i/validate.py
.venv/bin/python experiments/g6i/resources.py
.venv/bin/python experiments/g6i/report.py
.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib,json
base=Path('manifests/g6i')
paths=list(base.rglob('*'))+list(Path('experiments/g6i').glob('*.py'))+list(Path('experiments/g6i').glob('*.sh'))+list(Path('reports').glob('G6I_*.md'))+[Path('experiments/g6i/freeze.json')]
out=base/'sha256.json'
data={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file() and p!=out and p.name!='.DS_Store'}
out.write_text(json.dumps(data,indent=2)+'\n')
PY
