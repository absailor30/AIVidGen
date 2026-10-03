#!/bin/bash
# Build the SageAttention wheel once on an L40 (sm_89) and keep it on the volume.
# The wheel only works on the GPU architecture it was built for.
cd /root && git clone https://github.com/thu-ml/SageAttention.git && cd SageAttention
export TORCH_CUDA_ARCH_LIST="8.9" EXT_PARALLEL=4 NVCC_APPEND_FLAGS="--threads 8" MAX_JOBS=16
pip wheel . --no-build-isolation --no-deps -w /root/wheels
mkdir -p /workspace/wheels && cp /root/wheels/sageattention-*.whl /workspace/wheels/
