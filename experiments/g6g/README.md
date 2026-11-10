# Reproduce G6-G

Run from the repository root with the versions recorded in manifests/g6g/provenance.json. Supply the two verified TIGER zip files in GEOMETRY and a cache directory in MARYLAND. Historical project inputs are named in provenance.json. The NYC service metadata snapshot is included. No model or prediction raster is required from the historical seal.

```sh
.venv/bin/python experiments/g6g/design.py "$GEOMETRY"
.venv/bin/python experiments/g6g/exposure.py "$GEOMETRY"
.venv/bin/python experiments/g6g/validate.py "$GEOMETRY"
.venv/bin/python experiments/g6g/finalize.py "$GEOMETRY"
.venv/bin/python experiments/g6g/external.py "$MARYLAND"
.venv/bin/python -m unittest discover -s tests
shasum -a 256 -c manifests/g6g/SHA256SUMS
```

The external check requests public metadata and TIFF header ranges. Offline NYC design and Monte Carlo stages consume archived tables and geometry. The offline-tests receipt records the original run time. Floating-point geometry and TIFF library versions affect exact byte reproducibility. Grid ordering and output weights are frozen. SHA256SUMS verifies distributed artifacts including reports.
