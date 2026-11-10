# RQ2. Intersectional differences in tract-level measurement error

The four cells cross neighborhood poverty and non-Hispanic Black population share. The extreme contrast compares high–high with low–low. The factorial contrast subtracts both single-high cells from the sum of the high–high and low–low cells. Positive absolute-error contrasts denote greater error for the specified contrast. Signed-error contrasts give the direction of bias.

The unrestricted target includes 265 eligible tracts. Common-morphology weights describe 221 tracts in a restricted population. Each family and scope has eight prespecified Holm-adjusted tests. Spatial pointwise intervals, kernel sensitivities, effective blocks and block deletions accompany all estimates in rq2_contrasts.csv.

| scope | family | outcome | metric | contrast | estimate | primary_lo | primary_hi | holm_p |
|---|---|---|---|---|---|---|---|---|
| all | cnn | constructed | signed | extreme | -0.444 | -1.213 | 0.326 | 1.0 |
| all | cnn | constructed | signed | factorial | 0.019 | -0.757 | 0.795 | 1.0 |
| all | cnn | constructed | absolute | extreme | -0.344 | -1.029 | 0.341 | 1.0 |
| all | cnn | constructed | absolute | factorial | 0.051 | -0.630 | 0.731 | 1.0 |
| all | ijepa | constructed | signed | extreme | -0.001 | -2.238 | 2.235 | 1.0 |
| all | ijepa | constructed | signed | factorial | 2.310 | -0.003 | 4.623 | 0.2900276152743324 |
| all | ijepa | constructed | absolute | extreme | -0.211 | -2.439 | 2.017 | 1.0 |
| all | ijepa | constructed | absolute | factorial | -2.365 | -4.574 | -0.156 | 0.2900276152743324 |
| all | segformer | constructed | signed | extreme | -0.379 | -1.045 | 0.288 | 1.0 |
| all | segformer | constructed | signed | factorial | -0.061 | -0.889 | 0.766 | 1.0 |
| all | segformer | constructed | absolute | extreme | 0.152 | -0.164 | 0.469 | 1.0 |
| all | segformer | constructed | absolute | factorial | -0.111 | -0.553 | 0.330 | 1.0 |
| all | yolo | constructed | signed | extreme | -0.929 | -1.926 | 0.068 | 0.38840538043606576 |
| all | yolo | constructed | signed | factorial | 0.015 | -0.790 | 0.819 | 1.0 |
| all | yolo | constructed | absolute | extreme | -0.800 | -1.576 | -0.023 | 0.31194607113564005 |
| all | yolo | constructed | absolute | factorial | 0.147 | -0.562 | 0.856 | 1.0 |
| all | cnn | vegetation | signed | extreme | 0.320 | -0.469 | 1.108 | 1.0 |
| all | cnn | vegetation | signed | factorial | -0.032 | -0.767 | 0.702 | 1.0 |
| all | cnn | vegetation | absolute | extreme | -0.271 | -0.955 | 0.413 | 1.0 |
| all | cnn | vegetation | absolute | factorial | 0.101 | -0.533 | 0.736 | 1.0 |
| all | ijepa | vegetation | signed | extreme | -0.118 | -2.207 | 1.970 | 1.0 |
| all | ijepa | vegetation | signed | factorial | -2.128 | -4.160 | -0.097 | 0.2900276152743324 |
| all | ijepa | vegetation | absolute | extreme | -0.164 | -2.262 | 1.935 | 1.0 |
| all | ijepa | vegetation | absolute | factorial | -2.173 | -4.172 | -0.174 | 0.2900276152743324 |
| all | segformer | vegetation | signed | extreme | 0.342 | -0.350 | 1.035 | 1.0 |
| all | segformer | vegetation | signed | factorial | -0.049 | -0.835 | 0.737 | 1.0 |
| all | segformer | vegetation | absolute | extreme | 0.071 | -0.235 | 0.376 | 1.0 |
| all | segformer | vegetation | absolute | factorial | -0.034 | -0.508 | 0.439 | 1.0 |
| all | yolo | vegetation | signed | extreme | 0.925 | -0.067 | 1.917 | 0.38840538043606576 |
| all | yolo | vegetation | signed | factorial | -0.022 | -0.776 | 0.731 | 1.0 |
| all | yolo | vegetation | absolute | extreme | -0.837 | -1.613 | -0.060 | 0.29575364255559594 |
| all | yolo | vegetation | absolute | factorial | 0.348 | -0.354 | 1.050 | 1.0 |
| balanced_hull | cnn | constructed | signed | extreme | -0.555 | -1.389 | 0.278 | 1.0 |
| balanced_hull | cnn | constructed | signed | factorial | -0.041 | -0.953 | 0.872 | 1.0 |
| balanced_hull | cnn | constructed | absolute | extreme | -0.451 | -1.186 | 0.283 | 1.0 |
| balanced_hull | cnn | constructed | absolute | factorial | -0.004 | -0.822 | 0.814 | 1.0 |
| balanced_hull | ijepa | constructed | signed | extreme | -0.379 | -2.994 | 2.236 | 1.0 |
| balanced_hull | ijepa | constructed | signed | factorial | 1.379 | -1.544 | 4.302 | 1.0 |
| balanced_hull | ijepa | constructed | absolute | extreme | 0.288 | -2.338 | 2.914 | 1.0 |
| balanced_hull | ijepa | constructed | absolute | factorial | -1.556 | -4.255 | 1.144 | 1.0 |
| balanced_hull | segformer | constructed | signed | extreme | -0.499 | -1.170 | 0.172 | 0.9188074044042357 |
| balanced_hull | segformer | constructed | signed | factorial | -0.131 | -1.168 | 0.906 | 1.0 |
| balanced_hull | segformer | constructed | absolute | extreme | 0.067 | -0.280 | 0.413 | 1.0 |
| balanced_hull | segformer | constructed | absolute | factorial | -0.267 | -0.850 | 0.316 | 1.0 |
| balanced_hull | yolo | constructed | signed | extreme | -1.100 | -2.153 | -0.046 | 0.29823963977132806 |
| balanced_hull | yolo | constructed | signed | factorial | -0.043 | -1.311 | 1.225 | 1.0 |
| balanced_hull | yolo | constructed | absolute | extreme | -0.891 | -1.759 | -0.023 | 0.29823963977132806 |
| balanced_hull | yolo | constructed | absolute | factorial | 0.068 | -1.114 | 1.251 | 1.0 |
| balanced_hull | cnn | vegetation | signed | extreme | 0.540 | -0.269 | 1.350 | 1.0 |
| balanced_hull | cnn | vegetation | signed | factorial | 0.016 | -0.851 | 0.883 | 1.0 |
| balanced_hull | cnn | vegetation | absolute | extreme | -0.438 | -1.150 | 0.275 | 1.0 |
| balanced_hull | cnn | vegetation | absolute | factorial | -0.017 | -0.797 | 0.763 | 1.0 |
| balanced_hull | ijepa | vegetation | signed | extreme | 0.344 | -2.201 | 2.889 | 1.0 |
| balanced_hull | ijepa | vegetation | signed | factorial | -1.359 | -4.126 | 1.408 | 1.0 |
| balanced_hull | ijepa | vegetation | absolute | extreme | 0.266 | -2.286 | 2.818 | 1.0 |
| balanced_hull | ijepa | vegetation | absolute | factorial | -1.548 | -4.078 | 0.982 | 1.0 |
| balanced_hull | segformer | vegetation | signed | extreme | 0.494 | -0.147 | 1.135 | 0.9188074044042357 |
| balanced_hull | segformer | vegetation | signed | factorial | 0.016 | -0.848 | 0.881 | 1.0 |
| balanced_hull | segformer | vegetation | absolute | extreme | -0.010 | -0.372 | 0.351 | 1.0 |
| balanced_hull | segformer | vegetation | absolute | factorial | -0.201 | -0.762 | 0.360 | 1.0 |
| balanced_hull | yolo | vegetation | signed | extreme | 1.112 | 0.083 | 2.142 | 0.2977999035678995 |
| balanced_hull | yolo | vegetation | signed | factorial | -0.001 | -1.131 | 1.128 | 1.0 |
| balanced_hull | yolo | vegetation | absolute | extreme | -0.877 | -1.740 | -0.015 | 0.29823963977132806 |
| balanced_hull | yolo | vegetation | absolute | factorial | 0.112 | -0.962 | 1.186 | 1.0 |

Population composition comes from tract-level ACS estimates. These contrasts concern the accuracy of neighborhood measurements. Attribution to individuals or discrimination by a particular mechanism is unidentifiable. Common-morphology weighting balances the specified first moments only.
