# ============================================================
# config.py — Astro Video Workflow Configuration
# ============================================================

NIM_API_KEY    = "YOUR_NIM_API_KEY"            # Get from build.nvidia.com
NIM_BASE_URL   = "https://integrate.api.nvidia.com/v1"
NIM_MODEL      = "deepseek-ai/deepseek-v4-0324"

MPT_HOST       = "http://localhost:8080"        # MoneyPrinterTurbo / AIVidGen

OUTPUT_DIR     = "./output_videos"              # Where downloaded videos are saved

# Default voices (used if queue.txt line has no voice column)
DEFAULT_HINDI_VOICE   = "hi-IN-MadhurNeural"
DEFAULT_ENGLISH_VOICE = "en-IN-PrabhatNeural"

# Video settings
VIDEO_ASPECT_RATIO = "9:16"    # Reels / Shorts format
VIDEO_DURATION     = 60        # seconds

# Queue files
QUEUE_FILE = "queue.txt"
LOG_FILE   = "queue_log.txt"
