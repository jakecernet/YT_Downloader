import shutil
from yt_dlp import YoutubeDL


def download_video(url: str, max_height: int = 1080) -> bool:
    if not url or not url.strip():
        print("Error: URL cannot be empty.")
        return False

    # ffmpeg is required to merge the separate video and audio streams.
    if not shutil.which('ffmpeg'):
        print(
            "Error: ffmpeg was not found.\n"
            "ffmpeg is required to merge the separate video and audio streams\n"
            "that YouTube uses for 720p and above.\n"
            "Install it from https://ffmpeg.org and make sure it is in your PATH."
        )
        return False

    ydl_opts = {
        # ── Format selection ──────────────────────────────────────────────────
        # [acodec=none]  = video-only (no embedded audio) — excludes combined streams
        # [vcodec=none]  = audio-only (no embedded video) — excludes combined streams
        'format': (
            f'bestvideo[acodec=none][height<={max_height}]'
            f'+bestaudio[vcodec=none]'
            f'/bestvideo[acodec=none]+bestaudio[vcodec=none]'
        ),
        # Remux merged streams into mp4 without re-encoding the video track.
        # ffmpeg re-encodes audio only when necessary (e.g. Opus → AAC).
        'merge_output_format': 'mp4',

        # ── Output ────────────────────────────────────────────────────────────
        'outtmpl':          '%(title)s [%(id)s].%(ext)s',
        'restrictfilenames': True,   # replace spaces / special chars

        # ── Post-processing ───────────────────────────────────────────────────
        'writethumbnail': True,
        'postprocessors': [
            # Embed video title, uploader, date, etc. into the mp4 container
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            # Embed thumbnail as cover art (requires mutagen; skipped if absent)
            {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
        ],

        # ── Extraction ────────────────────────────────────────────────────────
        # android_vr is the default yt-dlp YouTube client and provides
        # separate high-quality streams without needing a JS runtime.
        'extractor_args': {
            'youtube': {'player_client': ['android_vr']},
        },

        # ── Reliability ───────────────────────────────────────────────────────
        'socket_timeout':  30,
        'ignoreerrors':    False,
        'quiet':           False,
        'no_warnings':     False,
    }

    print(f"Downloading up to {max_height}p MP4…")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = info.get('title', 'Unknown')

        # Report the resolution that was actually downloaded
        actual_height = None
        for fmt in (info.get('requested_formats') or []):
            if fmt.get('vcodec') not in (None, 'none'):
                actual_height = fmt.get('height')
                break
        if actual_height is None:
            actual_height = info.get('height')

        res_str = f" at {actual_height}p" if actual_height else ""
        print(f"\n'{title}' downloaded successfully{res_str}!")
        return True

    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        print("\nTroubleshooting tips:")
        print("  1. Check that your internet connection is stable.")
        print("  2. Update yt-dlp:  pip install --upgrade yt-dlp")
        print("  3. Verify the URL is correct and the video is publicly available.")
        print("  4. If YouTube is blocking requests, wait a moment and try again.")
        return False


if __name__ == "__main__":
    print("=== YouTube Video Downloader ===")
    video_url = input("\nEnter the YouTube video URL: ").strip()
    print()
    success = download_video(video_url)
    print("-" * 40)
    if success:
        print("Thank you for using the YouTube Downloader!")
    else:
        print("Download failed. Please try again.")