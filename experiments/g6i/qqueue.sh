set -eu
cd "$HOME/work/jev-g6i-v1"
while tmux has-session -t g6i-dense 2>/dev/null || tmux has-session -t g6i-qweights 2>/dev/null || tmux has-session -t g6i-vlmdeps 2>/dev/null; do sleep 30; done
test -f /tmp/g6i-qwen/VERIFIED
test -s prepared/dev.json
/tmp/g6i-vlm/bin/python -u qwen.py
python qwen_reduce.py
