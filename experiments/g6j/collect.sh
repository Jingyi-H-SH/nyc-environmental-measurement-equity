#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../.."
dest=manifests/g6j/run
mkdir -p "$dest"
ssh jev-g6-featurize 'cd ~/work/jev-g6j-v1 && test -f ijepa-receipt.json && test -f yolo-receipt.json && test -f segformer-receipt.json && test -f cnn-receipt.json && sha256sum results/*/*.json inputs/*.json *-receipt.json release.json > formal.sha256 && tar czf - results inputs *-receipt.json formal.sha256 release.json inputs.log evaluation.log device.csv' > "$dest/archive.tgz.tmp"
tar -xzf "$dest/archive.tgz.tmp" -C "$dest"
rm "$dest/archive.tgz.tmp"
(cd "$dest" && shasum -a 256 --quiet -c formal.sha256)
cmp manifests/g6j/release.json "$dest/release.json"
.venv/bin/python experiments/g6j/analyze.py "$dest/results"
.venv/bin/python experiments/g6j/distribution.py
.venv/bin/python experiments/g6j/secondary.py
.venv/bin/python experiments/g6j/summarize.py
