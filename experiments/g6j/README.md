# Held-out NYC neighborhood environmental measurement

The formal families are ResNet34 U-Net, SegFormer B0 and YOLO26n-sem. The frozen I-JEPA spatial readout is exploratory. The two geographic targets contain 265 technically eligible tracts and 221 morphology-comparable tracts. Bounds extend coverage accounting to the original 267. The analysis uses all eight mapped classes and two prespecified aggregates.

## Reproduce results without a GPU

Use the repository root, Python 3.12, and the pinned packages in `experiments/g6j/requirements-analysis.txt`. The formal prediction archive consists of one 8 × 8 area confusion matrix per tract and model. Rows are reference classes. Every RQ1–RQ3 estimate can be recovered from these counts and the geographic design. Independent reproduction does not require access to the Featurize account.

```sh
python experiments/g6j/test_statistics.py
python experiments/g6j/test_replay.py
python experiments/g6j/final_audit.py
python experiments/g6j/analyze.py manifests/g6j/run/results
python experiments/g6j/distribution.py
python experiments/g6j/secondary.py
python experiments/g6j/summarize.py
```

The synthetic replay checks an identity prediction on the frozen geometry. Its outputs are temporary and excluded from scientific results. To verify the released bytes use the SHA-256 manifest supplied at repository root before regenerating any files. Spreadsheet importers must preserve leading zeros in the intersectional cell and tract identifiers.

## Image-level reproduction

Use the official source versions and G6-H qualification manifests. The 2016 NYC images and original reference rasters are large source assets and are reacquired from their respective providers. G6-I contains training parameters, learned-checkpoint hashes, source-weight fingerprints, fixed split assignments and development receipts. A copy of all four trained checkpoints and development masks was additionally retained in the research archive. Byte-identical GPU refitting across differing CUDA libraries is not assumed.

Reconstruct the fixed input windows with `prepare_inputs.py` in the environment described by G6-H and G6-I. The subject of each model input is visible imagery of a neighborhood. Reference values determine the shared geographic mask and area-denominator check. Only the three RGB channels reach the model. A separate frozen release authorizes `infer.py` after G6-I receipts and spatial checks succeed. On Featurize, stage this script and the immutable release in the same G6-J directory. The original persistent directory layout is specified in the scripts. `launch.sh` and `collect.sh` use a researcher-configured SSH alias for that layout. No credentials are part of the archive.

RQ2 pointwise uncertainty uses weighted block residuals with spatial kernel sensitivity; the primary family has eight Holm-adjusted comparisons per model and target. RQ3 AI-minus-reference differences in the same signed contrasts are an exact algebraic identity. Block deletion intervals on nonlinear summaries are replication sensitivities. ACS estimates, historical imagery and mapped reference all have additional uncertainty.
