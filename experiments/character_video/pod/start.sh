#!/bin/bash
# WanGP on a RunPod L40/L40S pod. Lives on the pod's volume at /workspace/start.sh.
# Models download to the container disk each session (storing them costs more
# than it saves). What the volume keeps, to make the start quicker:
#   - the Python environment as one archive (thousands of small files are slow
#     over network storage; one file is fast)
#   - wgp_config.json, so WanGP opens on the last-used model (MiniMax) and
#     downloads only that one
#   - outputs and the SageAttention wheel
# Extra arguments go to wgp.py, e.g. to let Claude drive it over MCP:
#   bash /workspace/start.sh --mcp-webui --mcp-port 8000 --mcp-allow-read-file-system
set -e
TORCH="torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0"
ENV_DIR=/workspace/env
mkdir -p "$ENV_DIR" /workspace/outputs

cd /root
[ -d Wan2GP ] || git clone https://github.com/deepbeepmeep/Wan2GP.git
cd Wan2GP
rm -rf outputs && ln -s /workspace/outputs outputs
rm -f wgp_config.json && ln -s /workspace/wgp_config.json wgp_config.json

# The archive is keyed on requirements.txt + torch version + wheel, so a WanGP
# update that changes requirements rebuilds it instead of running stale packages.
KEY=$( (cat requirements.txt; echo "$TORCH"; ls /workspace/wheels 2>/dev/null) | md5sum | cut -c1-12)
ARCHIVE="$ENV_DIR/venv-$KEY.tar"

if [ -f "$ARCHIVE" ]; then
  echo "Restoring Python environment from the volume..."
  tar -xf "$ARCHIVE" -C /
  source /root/venv/bin/activate
else
  echo "No saved environment for this WanGP version; installing (first run is slow)..."
  python -m venv /root/venv
  source /root/venv/bin/activate
  pip install --upgrade pip
  pip install $TORCH --index-url https://download.pytorch.org/whl/cu128
  pip install -r requirements.txt hf_transfer
  ls /workspace/wheels/sageattention-*.whl >/dev/null 2>&1 && pip install /workspace/wheels/sageattention-*.whl
  pip cache purge || true
  echo "Saving environment to the volume..."
  rm -f "$ENV_DIR"/venv-*.tar          # keep only the current one (storage is billed)
  # Build locally, then one plain copy: the Global volume can't rename files.
  { tar -cf /root/venv.tar -C / root/venv && cp /root/venv.tar "$ARCHIVE" && rm -f /root/venv.tar; } \
    || { rm -f /root/venv.tar "$ARCHIVE"; echo "WARNING: could not save the environment; WanGP still starts."; }
fi

# Faster model downloads: parallel Xet transfers, and hf_transfer for the rest.
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_ENABLE_HF_TRANSFER=1

set +e
# The SageAttention wheel is built for Ada (sm_89: L40, L40S). It imports on other
# GPUs but crashes at run time, so only use it when the chip matches.
CC=$(python -c "import torch; print('%d.%d' % torch.cuda.get_device_capability())" 2>/dev/null)
echo "GPU compute capability: $CC"
if [ "$CC" = "8.9" ] && python -c "import sageattention" 2>/dev/null; then
  python wgp.py --profile 1 --attention sage2 --listen --server-port 7860 "$@"
else
  python wgp.py --profile 1 --listen --server-port 7860 "$@"
fi
