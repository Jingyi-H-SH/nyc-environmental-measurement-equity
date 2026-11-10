set -eu
python -m venv /tmp/g6i-vlm
p=/tmp/g6i-vlm/bin/pip
"$p" install --retries 2 --timeout 40 --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0 torchvision==0.23.0
"$p" install transformers==5.14.1 accelerate==1.15.0 pillow
