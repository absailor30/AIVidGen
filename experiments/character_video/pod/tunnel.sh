#!/bin/bash
# RunPod's HTTP proxy breaks Gradio buttons; a cloudflared quick tunnel works.
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
cloudflared tunnel --url http://localhost:7860
