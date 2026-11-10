# RQ1. Environmental measurement on held-out NYC geography

265 tracts in 55 spatial blocks contributed 3,324,001,222 common mapped pixels per family. The table gives pixel-pooled native macro-F1 and mean IoU and equal-tract mean compositional total variation in percentage points. I-JEPA is exploratory throughout.

| family | f1 | iou | total_variation_pp |
|---|---|---|---|
| cnn | 0.774 | 0.661 | 3.029 |
| ijepa | 0.446 | 0.326 | 16.558 |
| segformer | 0.817 | 0.700 | 3.164 |
| yolo | 0.767 | 0.637 | 4.102 |

Equal-tract signed error and absolute error, in pp. Intervals describe geographic replication under the prespecified spatial kernel.

| family | outcome | metric | estimate | lower | upper |
|---|---|---|---|---|---|
| cnn | constructed | signed | 1.583 | 1.235 | 1.931 |
| cnn | constructed | absolute | 1.661 | 1.347 | 1.975 |
| cnn | vegetation | signed | -1.457 | -1.780 | -1.134 |
| cnn | vegetation | absolute | 1.574 | 1.284 | 1.864 |
| ijepa | constructed | signed | -7.615 | -9.231 | -5.999 |
| ijepa | constructed | absolute | 7.761 | 6.217 | 9.305 |
| ijepa | vegetation | signed | 8.176 | 6.746 | 9.605 |
| ijepa | vegetation | absolute | 8.214 | 6.813 | 9.614 |
| segformer | constructed | signed | -0.146 | -0.554 | 0.262 |
| segformer | constructed | absolute | 0.970 | 0.889 | 1.051 |
| segformer | vegetation | signed | 0.198 | -0.197 | 0.593 |
| segformer | vegetation | absolute | 0.944 | 0.862 | 1.027 |
| yolo | constructed | signed | 2.411 | 2.102 | 2.721 |
| yolo | constructed | absolute | 2.511 | 2.231 | 2.791 |
| yolo | vegetation | signed | -2.290 | -2.583 | -1.996 |
| yolo | vegetation | absolute | 2.454 | 2.178 | 2.729 |

| family | outcome | reference_pixels | predicted_pixels | precision | recall | f1 | iou |
|---|---|---|---|---|---|---|---|
| cnn | tree | 573620200 | 547444786 | 0.813 | 0.776 | 0.794 | 0.659 |
| cnn | grass_shrub | 369237256 | 357516118 | 0.753 | 0.729 | 0.741 | 0.589 |
| cnn | bare_soil | 77954438 | 22303919 | 0.734 | 0.210 | 0.327 | 0.195 |
| cnn | water | 275375926 | 277456158 | 0.969 | 0.976 | 0.972 | 0.946 |
| cnn | building | 745125295 | 815957507 | 0.852 | 0.933 | 0.890 | 0.803 |
| cnn | road | 414152309 | 417950726 | 0.876 | 0.884 | 0.880 | 0.786 |
| cnn | other_impervious | 849707004 | 869728298 | 0.772 | 0.790 | 0.781 | 0.640 |
| cnn | rail | 18828794 | 15643710 | 0.887 | 0.737 | 0.805 | 0.673 |
| ijepa | tree | 573620200 | 996879176 | 0.427 | 0.742 | 0.542 | 0.371 |
| ijepa | grass_shrub | 369237256 | 267272502 | 0.477 | 0.345 | 0.401 | 0.251 |
| ijepa | bare_soil | 77954438 | 15 | 0.200 | 0.000 | 0.000 | 0.000 |
| ijepa | water | 275375926 | 207015518 | 0.949 | 0.713 | 0.814 | 0.687 |
| ijepa | building | 745125295 | 872646617 | 0.653 | 0.764 | 0.704 | 0.543 |
| ijepa | road | 414152309 | 465476857 | 0.594 | 0.668 | 0.629 | 0.459 |
| ijepa | other_impervious | 849707004 | 505048750 | 0.586 | 0.349 | 0.437 | 0.280 |
| ijepa | rail | 18828794 | 9661787 | 0.058 | 0.030 | 0.040 | 0.020 |
| segformer | tree | 573620200 | 619679410 | 0.756 | 0.817 | 0.785 | 0.647 |
| segformer | grass_shrub | 369237256 | 334335163 | 0.769 | 0.696 | 0.731 | 0.576 |
| segformer | bare_soil | 77954438 | 58164492 | 0.797 | 0.594 | 0.681 | 0.516 |
| segformer | water | 275375926 | 285347972 | 0.949 | 0.984 | 0.966 | 0.935 |
| segformer | building | 745125295 | 733724271 | 0.908 | 0.894 | 0.901 | 0.820 |
| segformer | road | 414152309 | 436826315 | 0.841 | 0.887 | 0.863 | 0.760 |
| segformer | other_impervious | 849707004 | 835695614 | 0.785 | 0.772 | 0.778 | 0.637 |
| segformer | rail | 18828794 | 20227985 | 0.802 | 0.862 | 0.831 | 0.711 |
| yolo | tree | 573620200 | 566981106 | 0.748 | 0.739 | 0.744 | 0.592 |
| yolo | grass_shrub | 369237256 | 328167575 | 0.725 | 0.644 | 0.682 | 0.517 |
| yolo | bare_soil | 77954438 | 39825726 | 0.854 | 0.436 | 0.577 | 0.406 |
| yolo | water | 275375926 | 273214411 | 0.965 | 0.957 | 0.961 | 0.925 |
| yolo | building | 745125295 | 751293151 | 0.879 | 0.886 | 0.882 | 0.790 |
| yolo | road | 414152309 | 436364894 | 0.829 | 0.874 | 0.851 | 0.740 |
| yolo | other_impervious | 849707004 | 904373438 | 0.733 | 0.780 | 0.755 | 0.607 |
| yolo | rail | 18828794 | 23780921 | 0.612 | 0.772 | 0.683 | 0.518 |

The native-class tables include rare outcomes. Land-cover aggregates can mask opposite-signed native errors.

Inference resources for each completed model

| family | tracts | windows | elapsed_seconds | peak_bytes |
|---|---|---|---|---|
| cnn | 265 | 17336 | 207.504 | 636009984 |
| segformer | 265 | 17336 | 206.706 | 788317696 |
| yolo | 265 | 17336 | 205.868 | 320132096 |
| ijepa | 265 | 17336 | 258.443 | 2822972416 |
