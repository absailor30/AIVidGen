"""Publish an already-rendered episode file (no rendering, no story queue).

For hand-made series episodes such as The Recipe Clause, which are rendered
outside the nightly pipeline. Reuses render_from_supabase's YouTube and
Instagram uploaders, so credentials and behaviour are identical.

Env:
  VIDEO_PATH        path of the mp4, relative to the repo checkout
  KIT_PATH          JSON publishing kit: youtube_title, youtube_description,
                    youtube_tags, instagram_caption, instagram_hashtags
  PLATFORM          "youtube" or "instagram"
  YOUTUBE_PUBLISH_AT  optional RFC3339 UTC time; YouTube uploads private and
                      goes public on its own at that moment
  plus the usual GOOGLE_* / SUPABASE_* / IG_* secrets.
"""
import json
import os
import sys

import render_from_supabase as rfs


def main():
    video = os.environ["VIDEO_PATH"]
    kit = json.load(open(os.environ["KIT_PATH"]))
    platform = os.environ["PLATFORM"].strip().lower()
    if not os.path.exists(video):
        sys.exit(f"[publish] Video not found: {video}")

    if platform == "youtube":
        video_id = rfs.upload_to_youtube(video, kit)
        if not video_id:
            sys.exit("[publish] YouTube upload returned no video id.")
        print(f"[publish] YouTube: https://youtu.be/{video_id}")
    elif platform == "instagram":
        sb = rfs.supabase_client()
        token = rfs.resolve_ig_token(sb)
        if not token or not os.environ.get("IG_USER_ID"):
            sys.exit("[publish] No usable Instagram token or IG_USER_ID.")
        name = os.path.splitext(os.path.basename(video))[0]
        storage_path, url = rfs.get_signed_video_url(sb, video, name)
        try:
            media_id = rfs.upload_to_instagram(url, kit, token)
        finally:
            rfs.delete_from_storage(sb, storage_path)
        if not media_id:
            sys.exit("[publish] Instagram did not publish.")
        print(f"[publish] Instagram media id: {media_id}")
    else:
        sys.exit(f"[publish] Unknown PLATFORM {platform!r}")


if __name__ == "__main__":
    main()
