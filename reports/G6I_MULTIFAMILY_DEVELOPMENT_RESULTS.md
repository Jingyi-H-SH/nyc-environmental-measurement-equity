# Prospective family execution

| Family | Status | Peak allocated GiB | Elapsed seconds in last attempt |
| --- | --- | ---: | ---: |
| cnn | COMPLETE | 1.484 | 392.721 |
| segformer | COMPLETE | 2.406 | 552.209 |
| yolo | COMPLETE | 0.738 | 582.359 |
| ijepa | COMPLETE | 2.632 | 3993.105 |
| dinov3 | BLOCKED — official gated weight unavailable | — | — |
| qwen | COMPLETE | 18.125 | 6667.021 |

All dense families use 5,196 positive-area windows on 163 fitting tracts, eight passes and one shared ordering. The planned development census comprises 6,314 windows on 53 tracts. Tract-level class shares use 1,368,453,171 paired pixels. Input manifests and per-window digests reside in the Featurize job directory. Four distinct dense backends passed independent synthetic forward and backward checks. Synthetic losses do not estimate geographic performance. Pinned family configurations, input normalization, fitted parameters and environment are archived with the run.

The persistent Featurize directory is `~/work/jev-g6i-v1`. Each completed dense backend has a final checkpoint including optimizer state, individual development masks, a tract confusion file and a completion receipt. Runtime covers loading, fitting and inference in that invocation. Retained-instance allocation and billed charges can differ. [Receipts and logs](../manifests/g6i/run/) · [Frozen configuration](../experiments/g6i/freeze.json)

## Checkpoint provenance and use

| Family | External initialization and interface | Source terms |
|---|---|---|
| CNN | ImageNet ResNet-34 IMAGENET1K_V1, new U-Net decoder | [Torchvision weights and dataset-use notice](https://docs.pytorch.org/vision/stable/models.html) |
| SegFormer | NVIDIA ADE B0, revision `489d5cd`, reset classifier | [Model card](https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512) · [NVIDIA research license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE) |
| YOLO | YOLO26n-sem semantic initialization, eight logits | [Ultralytics license](https://www.ultralytics.com/license) |
| I-JEPA | Frozen ViT-H/14 revision `f157467`, trained decoder | [CC BY-NC 4.0 model card](https://huggingface.co/facebook/ijepa_vith14_1k) |
| DINOv3 | SAT493M ViT-L/16 revision `f692fa4`, official client HTTP 401 and no cached authorized copy | [Gated model card and terms](https://huggingface.co/facebook/dinov3-vitl16-pretrain-sat493m) |
| Qwen | Qwen3.5-9B revision `c202236`, image-only structured shares | [Apache 2.0 model card](https://huggingface.co/Qwen/Qwen3.5-9B) |

Source-byte digests and environment locks accompany the run. Prior NYC-fitted SegFormer weights were excluded. These records document research execution; redistribution of third-party materials requires review of the applicable terms.

[Actual training steps, end-to-end throughput, sampled device utilization, power and memory](../manifests/g6i/resources.csv). End-to-end throughput divides all processed training and development windows by runtime, including checkpoint I/O. Sampled power estimates cover the device alone. They exclude host power and retained-instance idle time. Active-time cost uses the preceding G6-H observation of ¥3 per instance-hour. The provider invoice and the total cost of keeping the instance allocated are unverified.
