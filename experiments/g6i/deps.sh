#!/usr/bin/env bash
set -eu
python -m venv --system-site-packages /tmp/g6i-env
source /tmp/g6i-env/bin/activate
pip install --disable-pip-version-check 'numpy==1.26.4' 'opencv-python==4.10.0.84' 'ultralytics==8.4.208' 'transformers==4.57.6' 'safetensors==0.6.2' 'huggingface_hub==0.36.0'
pip freeze > environment.txt
