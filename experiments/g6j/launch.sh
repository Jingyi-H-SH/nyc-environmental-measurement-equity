#!/usr/bin/env bash
# Run only after the complete G6-I collection and separate G6-J release.
set -eu
cd "$(dirname "$0")/../.."
.venv/bin/python experiments/g6i/validate.py
.venv/bin/python experiments/g6j/test_statistics.py
.venv/bin/python experiments/g6j/freeze.py
scp experiments/g6j/infer.py experiments/g6j/evaluate.sh manifests/g6j/release.json jev-g6-featurize:work/jev-g6j-v1/
ssh jev-g6-featurize 'set -eu
cd ~/work/jev-g6i-v1
sha256sum --quiet -c dense_source.sha
sha256sum --quiet -c resnet.sha
sha256sum --quiet -c ijepa.sha
cd ~/work/jev-g6j-v1
grep -q "^COMPLETE 265" inputs.log
test ! -f ijepa-receipt.json
tmux new-session -d -s g6j-evaluation "bash evaluate.sh >> evaluation.log 2>&1"'
