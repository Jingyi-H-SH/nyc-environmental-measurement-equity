# RQ2 precision for the frozen evaluation

| Family | Outcome | Error | Dev SD (pp) | Dev block ICC | 265 extreme half-width (pp) | 265 factorial half-width (pp) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| cnn | constructed | absolute_pp | 1.522 | 0.659 | 1.023 | 1.477 |
| cnn | constructed | signed_pp | 2.653 | 0.875 | 1.953 | 2.820 |
| cnn | vegetation | absolute_pp | 1.491 | 0.694 | 1.018 | 1.470 |
| cnn | vegetation | signed_pp | 2.568 | 0.861 | 1.880 | 2.715 |
| ijepa | constructed | absolute_pp | 5.367 | 0.743 | 3.745 | 5.407 |
| ijepa | constructed | signed_pp | 5.567 | 0.756 | 3.906 | 5.640 |
| ijepa | vegetation | absolute_pp | 5.092 | 0.747 | 3.558 | 5.137 |
| ijepa | vegetation | signed_pp | 5.263 | 0.756 | 3.692 | 5.330 |
| segformer | constructed | absolute_pp | 1.087 | 0.191 | 0.550 | 0.793 |
| segformer | constructed | signed_pp | 1.531 | 0.398 | 0.896 | 1.293 |
| segformer | vegetation | absolute_pp | 1.264 | 0.418 | 0.749 | 1.080 |
| segformer | vegetation | signed_pp | 1.727 | 0.573 | 1.114 | 1.607 |
| yolo | constructed | absolute_pp | 2.286 | 0.541 | 1.450 | 2.093 |
| yolo | constructed | signed_pp | 3.757 | 0.768 | 2.649 | 3.824 |
| yolo | vegetation | absolute_pp | 1.941 | 0.780 | 1.375 | 1.986 |
| yolo | vegetation | signed_pp | 2.902 | 0.688 | 1.976 | 2.853 |

[Class-specific projections for both scopes](../manifests/g6i/projected_precision.csv).

Planning targets are half-widths of 3 pp (11−00) and 5 pp (factorial). G6-H's central SD 5 pp, ICC 0.25 projects 2.65/3.82 pp across the 265 eligible tracts and 3.00/4.24 pp among 221 morphology-comparable tracts. Its stress scenario projects 3.41/4.92 and 3.81/5.29 pp, respectively. The 221-tract estimate conditions on common morphology; spatial weighting does not restore omitted geography. For the original 267-tract equal-cell target, excluded geography plus unpaired mapped area contributes worst-case signed-error identification spans of 1.285/3.461 pp. These spans are distinct from sampling half-widths.

Development SD is the observed tract-level SD. The block ICC uses an unbalanced one-way random-intercept method-of-moments estimate, with negative between-block variance truncated at zero. This plug-in calculation assumes development variance transports to the sealed cohort. Development cell 01 contains only three tracts in three blocks. Retain frozen stress projections and disclose instability. RQ3 signed gap distortion inherits the corresponding RQ2 signed-error contrast. No final errors enter these calculations. [G6-H qualification and support](G6H_INTERSECTIONAL_PRECISION_RECHECK.md) · [Original-target sensitivity](../manifests/g6h/original_weight_sensitivity.csv)

| Model | Geography | Extreme range (pp) | Factorial range (pp) | Within planned width |
| --- | --- | ---: | ---: | ---: |
| cnn | all | 1.02–1.95 | 1.47–2.82 | 8/8 |
| cnn | balanced_hull | 1.11–2.11 | 1.48–2.78 | 8/8 |
| ijepa | all | 3.56–3.91 | 5.14–5.64 | 0/8 |
| ijepa | balanced_hull | 3.86–4.24 | 5.14–5.64 | 0/8 |
| segformer | all | 0.55–1.11 | 0.79–1.61 | 8/8 |
| segformer | balanced_hull | 0.63–1.22 | 0.90–1.65 | 8/8 |
| yolo | all | 1.38–2.65 | 1.99–3.82 | 8/8 |
| yolo | balanced_hull | 1.49–2.87 | 1.98–3.82 | 8/8 |

Ranges span both environmental domains and signed/absolute errors. Each denominator counts prespecified projections. The limits address planned precision and do not test for differential error.

Full-area Qwen error variance and the corresponding primary RQ2 precision are unidentified from partially returned windows. Its failure bounds are retained. Applying the full-area weights to conditional observed-window errors would change the estimand.
