#!/bin/bash
# WanGP on a RunPod L40 pod. Lives on the pod's volume at /workspace/start.sh.
# Models download to the container disk (100GB) each session; only outputs and
# the SageAttention wheel live on the volume.
cd /root
[ -d Wan2GP ] || git clone https://github.com/deepbeepmeep/Wan2GP.git
cd Wan2GP
mkdir -p /workspace/outputs && rm -rf outputs && ln -s /workspace/outputs outputs
pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
if ls /workspace/wheels/sageattention-*.whl >/dev/null 2>&1; then
  pip install /workspace/wheels/sageattention-*.whl
  python wgp.py --profile 1 --attention sage2 --listen --server-port 7860
else
  python wgp.py --profile 1 --listen --server-port 7860
fi
