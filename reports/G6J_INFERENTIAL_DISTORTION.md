# RQ3. Consequences for estimated neighborhood inequalities

All reported gaps use identical tract weights for AI and mapped reference. AI minus reference reproduces the RQ2 signed-error contrast exactly. This identity gives one evidence chain and one statistical test.

| scope | family | outcome | contrast | reference_gap | ai_gap | distortion | lower | upper | holm_p |
|---|---|---|---|---|---|---|---|---|---|
| all | cnn | constructed | extreme | -0.143 | -0.587 | -0.444 | -1.213 | 0.326 | 1.0 |
| all | cnn | constructed | factorial | -1.324 | -1.305 | 0.019 | -0.757 | 0.795 | 1.0 |
| all | ijepa | constructed | extreme | -0.143 | -0.144 | -0.001 | -2.238 | 2.235 | 1.0 |
| all | ijepa | constructed | factorial | -1.324 | 0.986 | 2.310 | -0.003 | 4.623 | 0.2900276152743324 |
| all | segformer | constructed | extreme | -0.143 | -0.522 | -0.379 | -1.045 | 0.288 | 1.0 |
| all | segformer | constructed | factorial | -1.324 | -1.385 | -0.061 | -0.889 | 0.766 | 1.0 |
| all | yolo | constructed | extreme | -0.143 | -1.072 | -0.929 | -1.926 | 0.068 | 0.38840538043606576 |
| all | yolo | constructed | factorial | -1.324 | -1.309 | 0.015 | -0.790 | 0.819 | 1.0 |
| all | cnn | vegetation | extreme | 0.104 | 0.424 | 0.320 | -0.469 | 1.108 | 1.0 |
| all | cnn | vegetation | factorial | -0.291 | -0.323 | -0.032 | -0.767 | 0.702 | 1.0 |
| all | ijepa | vegetation | extreme | 0.104 | -0.014 | -0.118 | -2.207 | 1.970 | 1.0 |
| all | ijepa | vegetation | factorial | -0.291 | -2.419 | -2.128 | -4.160 | -0.097 | 0.2900276152743324 |
| all | segformer | vegetation | extreme | 0.104 | 0.446 | 0.342 | -0.350 | 1.035 | 1.0 |
| all | segformer | vegetation | factorial | -0.291 | -0.340 | -0.049 | -0.835 | 0.737 | 1.0 |
| all | yolo | vegetation | extreme | 0.104 | 1.029 | 0.925 | -0.067 | 1.917 | 0.38840538043606576 |
| all | yolo | vegetation | factorial | -0.291 | -0.313 | -0.022 | -0.776 | 0.731 | 1.0 |
| balanced_hull | cnn | constructed | extreme | 0.002 | -0.554 | -0.555 | -1.389 | 0.278 | 1.0 |
| balanced_hull | cnn | constructed | factorial | 0.002 | -0.038 | -0.041 | -0.953 | 0.872 | 1.0 |
| balanced_hull | ijepa | constructed | extreme | 0.002 | -0.377 | -0.379 | -2.994 | 2.236 | 1.0 |
| balanced_hull | ijepa | constructed | factorial | 0.002 | 1.382 | 1.379 | -1.544 | 4.302 | 1.0 |
| balanced_hull | segformer | constructed | extreme | 0.002 | -0.497 | -0.499 | -1.170 | 0.172 | 0.9188074044042357 |
| balanced_hull | segformer | constructed | factorial | 0.002 | -0.129 | -0.131 | -1.168 | 0.906 | 1.0 |
| balanced_hull | yolo | constructed | extreme | 0.002 | -1.098 | -1.100 | -2.153 | -0.046 | 0.29823963977132806 |
| balanced_hull | yolo | constructed | factorial | 0.002 | -0.040 | -0.043 | -1.311 | 1.225 | 1.0 |
| balanced_hull | cnn | vegetation | extreme | -0.002 | 0.539 | 0.540 | -0.269 | 1.350 | 1.0 |
| balanced_hull | cnn | vegetation | factorial | -0.002 | 0.014 | 0.016 | -0.851 | 0.883 | 1.0 |
| balanced_hull | ijepa | vegetation | extreme | -0.002 | 0.342 | 0.344 | -2.201 | 2.889 | 1.0 |
| balanced_hull | ijepa | vegetation | factorial | -0.002 | -1.361 | -1.359 | -4.126 | 1.408 | 1.0 |
| balanced_hull | segformer | vegetation | extreme | -0.002 | 0.492 | 0.494 | -0.147 | 1.135 | 0.9188074044042357 |
| balanced_hull | segformer | vegetation | factorial | -0.002 | 0.014 | 0.016 | -0.848 | 0.881 | 1.0 |
| balanced_hull | yolo | vegetation | extreme | -0.002 | 1.111 | 1.112 | 0.083 | 2.142 | 0.2977999035678995 |
| balanced_hull | yolo | vegetation | factorial | -0.002 | -0.004 | -0.001 | -1.131 | 1.128 | 1.0 |

Secondary distributional results. Rank shift is the fraction of tracts moving at least ten percentile points.

| scope | family | outcome | statistic | estimate | lower | upper |
|---|---|---|---|---|---|---|
| all | cnn | constructed | spearman | 0.9942222623454005 | 0.9917365290022642 | 0.9967079956885367 |
| all | cnn | constructed | rank_shift_ge10_fraction | 0.0 | -0.03360156839714545 | 0.03360156839714545 |
| all | cnn | vegetation | spearman | 0.99344458917448 | 0.9908409518344405 | 0.9960482265145194 |
| all | cnn | vegetation | rank_shift_ge10_fraction | 0.003773584905660378 | -0.01641443268628579 | 0.023961602497606545 |
| all | ijepa | constructed | spearman | 0.9510336733772682 | 0.9249672433427448 | 0.9771001034117915 |
| all | ijepa | constructed | rank_shift_ge10_fraction | 0.23773584905660375 | 0.07680965250838914 | 0.3986620456048183 |
| all | ijepa | vegetation | spearman | 0.9442106552831481 | 0.9117462658028213 | 0.9766750447634749 |
| all | ijepa | vegetation | rank_shift_ge10_fraction | 0.2528301886792453 | 0.11748662874347929 | 0.3881737486150113 |
| all | segformer | constructed | spearman | 0.9940900708030799 | 0.9915629529000504 | 0.9966171887061094 |
| all | segformer | constructed | rank_shift_ge10_fraction | 0.003773584905660378 | -0.019147861042718234 | 0.026695030854038987 |
| all | segformer | vegetation | spearman | 0.9942216175086085 | 0.991566835307082 | 0.996876399710135 |
| all | segformer | vegetation | rank_shift_ge10_fraction | 0.003773584905660378 | -0.018065714166689957 | 0.02561288397801071 |
| all | yolo | constructed | spearman | 0.9906956499310026 | 0.9867637055213239 | 0.9946275943406813 |
| all | yolo | constructed | rank_shift_ge10_fraction | 0.022641509433962263 | -0.0316443485727185 | 0.07692736744064303 |
| all | yolo | vegetation | spearman | 0.9881401617250674 | 0.9822554929547446 | 0.9940248304953901 |
| all | yolo | vegetation | rank_shift_ge10_fraction | 0.033962264150943396 | -0.018379668201872375 | 0.08630419650375917 |
| balanced_hull | cnn | constructed | spearman | 0.9916795933564062 | 0.987885293516774 | 0.9954738931960384 |
| balanced_hull | cnn | constructed | rank_shift_ge10_fraction | 0.012053642991601136 | -0.020707759203684083 | 0.04481504518688636 |
| balanced_hull | cnn | vegetation | spearman | 0.9906317002650941 | 0.9868954841745424 | 0.9943679163556457 |
| balanced_hull | cnn | vegetation | rank_shift_ge10_fraction | 0.009293017074385887 | -0.03315734543194815 | 0.05174337958071992 |
| balanced_hull | ijepa | constructed | spearman | 0.9182303481106007 | 0.8752526547238357 | 0.9612080414973656 |
| balanced_hull | ijepa | constructed | rank_shift_ge10_fraction | 0.36655874222128293 | 0.2605535027699224 | 0.47256398167264346 |
| balanced_hull | ijepa | vegetation | spearman | 0.9226246931077435 | 0.8791520551414304 | 0.9660973310740567 |
| balanced_hull | ijepa | vegetation | rank_shift_ge10_fraction | 0.3677134847232406 | 0.18949445799172962 | 0.5459325114547516 |
| balanced_hull | segformer | constructed | spearman | 0.990387658832873 | 0.9866349755211095 | 0.9941403421446366 |
| balanced_hull | segformer | constructed | rank_shift_ge10_fraction | 0.007910552034475053 | -0.06550426290142534 | 0.08132536697037544 |
| balanced_hull | segformer | vegetation | spearman | 0.9913341524189287 | 0.9876444674164327 | 0.9950238374214248 |
| balanced_hull | segformer | vegetation | rank_shift_ge10_fraction | 0.01363411230933325 | -0.028350311034161843 | 0.055618535652828344 |
| balanced_hull | yolo | constructed | spearman | 0.9865934948994507 | 0.9805815469873624 | 0.992605442811539 |
| balanced_hull | yolo | constructed | rank_shift_ge10_fraction | 0.055805354154919044 | -0.017494088262491915 | 0.12910479657233 |
| balanced_hull | yolo | vegetation | spearman | 0.9847523402694721 | 0.9784078301905564 | 0.9910968503483878 |
| balanced_hull | yolo | vegetation | rank_shift_ge10_fraction | 0.05512069428541126 | -0.035939638686242975 | 0.1461810272570655 |

Worst-case identification bounds on signed gap distortion in the original 267-tract target include all unpaired mapped pixels and both omitted tracts. These bounds describe missing-area uncertainty separately from geographic replication.

| family | outcome | contrast | lower | upper |
|---|---|---|---|---|
| cnn | constructed | extreme | -1.125 | 0.160 |
| cnn | constructed | factorial | -1.750 | 1.711 |
| cnn | vegetation | extreme | -0.650 | 0.636 |
| cnn | vegetation | factorial | -2.090 | 1.371 |
| ijepa | constructed | extreme | -0.766 | 0.520 |
| ijepa | constructed | factorial | 0.463 | 3.925 |
| ijepa | vegetation | extreme | -0.992 | 0.293 |
| ijepa | vegetation | factorial | -4.098 | -0.637 |
| segformer | constructed | extreme | -1.078 | 0.208 |
| segformer | constructed | factorial | -1.838 | 1.624 |
| segformer | vegetation | extreme | -0.612 | 0.674 |
| segformer | vegetation | factorial | -2.099 | 1.363 |
| yolo | constructed | extreme | -1.600 | -0.314 |
| yolo | constructed | factorial | -1.745 | 1.716 |
| yolo | vegetation | extreme | -0.055 | 1.230 |
| yolo | vegetation | factorial | -2.089 | 1.372 |

Hypothetical greening screen among high-poverty tracts using training-side quartiles and a ten-percent capacity. Omitted and added count tracts changing selection relative to mapped reference. Sparse selected blocks limit uncertainty estimates.

| family | cell | n | reference_selected | selected_blocks | ai_selected | omitted | added | interval_status |
|---|---|---|---|---|---|---|---|---|
| cnn | all | 91 | 5 | 5 | 10 | 0 | 5 | insufficient_selected_block_support |
| cnn | 10 | 55 | 2 | 2 | 6 | 0 | 4 | insufficient_selected_block_support |
| cnn | 11 | 36 | 3 | 3 | 4 | 0 | 1 | insufficient_selected_block_support |
| ijepa | all | 91 | 5 | 5 | 6 | 3 | 4 | insufficient_selected_block_support |
| ijepa | 10 | 55 | 2 | 2 | 4 | 1 | 3 | insufficient_selected_block_support |
| ijepa | 11 | 36 | 3 | 3 | 2 | 2 | 1 | insufficient_selected_block_support |
| segformer | all | 91 | 5 | 5 | 10 | 1 | 6 | insufficient_selected_block_support |
| segformer | 10 | 55 | 2 | 2 | 7 | 0 | 5 | insufficient_selected_block_support |
| segformer | 11 | 36 | 3 | 3 | 3 | 1 | 1 | insufficient_selected_block_support |
| yolo | all | 91 | 5 | 5 | 10 | 0 | 5 | insufficient_selected_block_support |
| yolo | 10 | 55 | 2 | 2 | 5 | 0 | 3 | insufficient_selected_block_support |
| yolo | 11 | 36 | 3 | 3 | 5 | 0 | 2 | insufficient_selected_block_support |

All conditional Wasserstein distances, regression differences per ten percentage points, interaction leverage, and delete-one-block ranges are archived. Geographic replication intervals exclude ACS uncertainty, mapped-reference error, historical image dependence and unknown pretraining exposure. No citywide, health-outcome or causal extrapolation is identified.
