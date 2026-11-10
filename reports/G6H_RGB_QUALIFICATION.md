# reserve8: observed raw-image and reference qualification
Decision for the RGB prerequisite: **CONDITIONAL**. Actual source archives, decoded files and raster overlays, on Featurize. No model predictions were generated or inspected.
    
| split | frozen | qualify | blocks | qualified_blocks | paired_polygon_% | paired_land_% | min_polygon_% | min_land_% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev | 53 | 53 | 11 | 11 | 99.772 | 99.745 | 98.675 | 98.675 |
| test | 267 | 265 | 55 | 55 | 99.6 | 99.809 | 94.71 | 97.195 |
| train | 163 | 163 | 31 | 31 | 99.104 | 99.789 | 95.952 | 98.601 |

The original historical pairing counts (5 train, 2 development, 0 evaluation) are an inventory of prior processing. All 483 tracts intersect the official [NYC 2016 raw orthophoto index](https://data.cityofnewyork.us/City-Government/2016-Orthoimagery-Tile-Index/sms6-sm5p). The five official borough distributions supplied all 671 needed JP2s, verified by ZIP-member CRC and SHA-256 after acquisition. 1677 tract/file links; three index county labels pointed to a different ZIP. File member names and embedded bounds, rather than county guesses, resolved them. Source ZIPs and masks are now cached in instance-local scratch; receipts are persistent and copied to the repository. Preexisting web-tile caches are distinct from these raw files. [Source provenance](../manifests/g6h/sources/archive_sources.json) · [Per-file receipts](../manifests/g6h/source_files.csv).

7,291,724,513 polygon pixel centers; 7,269,946,985 inside decodable source footprints; 7,254,813,708 passed the conservative visible-pixel mask. 7,252,213,607 paired mapped pixels and 6,444,486,029 paired nonwater pixels. Each represents 0.25 ft². Outside the source footprint: 5,444,382.00 ft². Inside a footprint but masked (including interpolation seams): 3,783,319.25 ft². Valid RGB over unmapped reference accounts for another 650,025.25 ft². These three mutually exclusive reasons sum to the unpaired polygon area; none denotes a failed download. [Loss by borough and intersectional cell](../manifests/g6h/missing_distribution.csv) · [Area missing by reference class](../manifests/g6h/class_coverage.csv). No requested member is unresolved. [Tract manifest with quadrant-specific losses](../manifests/g6h/coverage.csv); eight-class denominators and paired counts are retained per tract.

The [city acquisition metadata](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_AerialImagery.md) describe the 2016 product. For coverage we used bands 1–3, valid data masks, excluded RGB triplets of all zero or all 255 and required four valid neighbors on a single raw tile. Some valid very dark/bright pixels may be conservatively lost. Comparing training-side display chips against all band orderings gave the lowest color MAE for (1,2,3) in 6/9 chips; see [chip-level differences](../manifests/g6h/run/channel_check.json). Rendering differences make this a diagnostic, not a guarantee of radiometric equivalence to web tiles.

Frozen inclusion: paired mapped / all polygon pixels **and** paired nonwater / reference nonwater ≥0.95. Qualifying counts at joint 90%, 95%, 99%: [(0.9, 483), (0.95, 481), (0.99, 466)]. The last thresholds are sensitivities, not new selections. Frozen records below the primary threshold: 36047017400, 36047017600. For each below-threshold tract, the two denominators can be inspected separately:

| geoid | split | cell | borough | paired_fraction | paired_land_fraction |
| --- | --- | --- | --- | --- | --- |
| 36047017400 | test | 00 | Brooklyn | 0.94948 | 0.97348 |
| 36047017600 | test | 10 | Brooklyn | 0.9471 | 0.97277 |

Independent checks compare all nine reference counts (unmapped and eight classes) against the original reference frame; no final errors were read.

No shared raw JP2 between splits and 0 shared level-20 delivery tile keys. Minimum distances (feet) of planned buffered input tile envelopes: {"train_dev": 3317.51, "train_test": 3415.02, "dev_test": 4062.19}. The ~4,004 ft minimum is a tract-polygon distance, not a window distance. Blocks are partition-disjoint but neighboring blocks are not assumed statistically independent. See [execution receipt](../manifests/g6h/execution_receipt.json).

Featurize profile: 21.50 GB downloaded (archive SHA-256s archived), 13.9 MB/s average over transfer; 6.78 GB of required compressed-in-JP2 members decoded; 2.10 GB mask cache; 57.5 aggregate decode-worker minutes. 28.5 elapsed minutes from source inventory to last tract receipt, including debugging and acquisition; the concurrent window enumeration and final QA have separate timestamps. Cold reproduction: allow 30 GB additional scratch plus the existing 97.74 GB native reference data member and geometry, 7 decode workers and 4 overlapping tract workers, approximately 1 hour(s) allowing network variability. The instance exposed 14 CPU cores and 60,262 MiB RAM. A [mid-decode snapshot](../manifests/g6h/run/resource_sample.txt) is included; it is not peak-memory telemetry. No CUDA workload. At the observed ¥3/instance-hour, source-to-tract elapsed allocation ≈¥1.43; this is not an invoice or the total cost of retaining the already running instance. No extra instance or storage was provisioned.
