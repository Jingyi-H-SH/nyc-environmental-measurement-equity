# Multidimensional measurement validity

| Family | Aggregate | Bias (pp) | MAE (pp) |
| --- | --- | ---: | ---: |
| cnn | constructed | -0.139 | 2.156 |
| cnn | vegetation | 0.175 | 2.078 |
| ijepa | constructed | -9.638 | 9.748 |
| ijepa | vegetation | 10.762 | 10.842 |
| qwen_valid_windows | constructed | 0.909 | 8.976 |
| qwen_valid_windows | vegetation | -4.500 | 7.385 |
| segformer | constructed | 0.901 | 1.398 |
| segformer | vegetation | -0.847 | 1.441 |
| yolo | constructed | -0.316 | 2.970 |
| yolo | vegetation | -0.633 | 2.228 |

Native errors are measured over the same tract pixels. Vegetation sums tree and grass/shrub. Constructed cover sums buildings, roads, other impervious surfaces and rail. Errors can cancel inside either sum. Pixel confusion retains all eight surface types, including distinctions among roads, buildings and other impervious areas. Share closure makes the eight errors dependent. Interpret hard-surface area in local environmental context. Prediction error includes differences between 2016 imagery and the 2017 reference map. Exposure of external pretraining to these locations is unknown.

| Family | Supported classes | Macro-F1 | Lowest class recall | Building → other impervious | Road → other impervious | Other impervious → building / road |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| cnn | 8 | 0.758 | bare_soil 0.412 | 7.1% | 9.3% | 10.5% / 5.6% |
| ijepa | 8 | 0.408 | bare_soil 0.000 | 10.6% | 7.2% | 21.7% / 17.3% |
| segformer | 8 | 0.760 | bare_soil 0.436 | 10.4% | 7.0% | 6.5% / 10.2% |
| yolo | 8 | 0.674 | bare_soil 0.222 | 13.5% | 10.9% | 8.5% / 5.8% |

Percentages condition on the native reference class. All native class counts, IoU, precision, recall and F1 are available in the [class table](../manifests/g6i/pixel_metrics.csv) and [eight-by-eight confusions](../manifests/g6i/confusion.csv). Pixel metrics give larger tracts more weight. The [signed and absolute share errors](../manifests/g6i/tract_measurements.csv) retain one observation per tract and outcome.

Qwen returned 2 valid arrays from 6,314 windows. Valid outputs cover 0.02% of all paired pixels. Tract share errors are conditional on returned area. The [matched comparisons](../manifests/g6i/qwen_matched_dense.csv) use identical windows for each dense–Qwen contrast. [Full-area signed-error bounds](../manifests/g6i/qwen_missing_area_bounds.csv) allow any missing-window share between 0 and 100%. Qwen supplies no pixel-level labels.

[Paired differences in tract MAE](../manifests/g6i/paired_development.csv) compare every completed dense pair on identical tracts, for each native class and aggregate. Leave-one-block ranges describe geographic sensitivity. They are not confidence intervals.

Of 53 development tracts, the reference includes rail in 6, bare soil in 11 and water in 7. Large pixel counts for these classes coexist with few supporting neighborhoods. See [class support by tract](../manifests/g6i/native_tract_support.csv).
