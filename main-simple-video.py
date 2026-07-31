import shutil
from yt_dlp import YoutubeDL


def check_requirements() -> bool:
    """Verify ffmpeg (required) and check for deno (recommended for YouTube)."""
    if not shutil.which('ffmpeg'):
        print(
            "Error: ffmpeg was not found.\n"
            "ffmpeg is required to merge separate video/audio streams and to remux files.\n"
            "Install it from https://ffmpeg.org and make sure it is in your PATH."
        )
        return False

    # yt-dlp supports several JS runtimes for solving YouTube's challenges.
    # Deno is enabled by default; the others need --js-runtimes to be enabled
    # but are still worth detecting so we don't nag people who already have one.
    js_runtimes = ('deno', 'node', 'bun', 'quickjs')
    if not any(shutil.which(rt) for rt in js_runtimes):
        print(
            "Note: no supported JavaScript runtime (deno, node, bun, or quickjs) was found on your PATH.\n"
            "YouTube now requires one of these to fetch some/all formats\n"
            "(other sites are unaffected). Deno is recommended and used automatically\n"
            "by yt-dlp once installed — no extra flags needed. Get it from:\n"
            "  https://docs.deno.com/runtime/getting_started/installation/\n"
        )

    return True


def download_video(url: str, max_height: int | None = None) -> bool:
    """
    Download the highest quality video from any site yt-dlp supports
    (YouTube, Vimeo, Twitter/X, TikTok, etc.), merging video+audio into
    a single MP4 file.

    max_height: optional cap (e.g. 1080). Leave as None for the highest
    quality available.
    """
    if not url or not url.strip():
        print("Error: URL cannot be empty.")
        return False

    if not check_requirements():
        return False

    height_filter = f'[height<={max_height}]' if max_height else ''

    ydl_opts = {
        # ── Format selection ──────────────────────────────────────────────
        # bv* = best video, INCLUDING formats that already contain audio
        #       (needed for sites that don't split streams the way YouTube does)
        # ba  = best standalone audio track
        # /b  = fall back to the single best pre-merged format if the above
        #       selectors find nothing suitable
        'format': f'bv*{height_filter}+ba/b{height_filter}',
        'merge_output_format': 'mp4',

        # ── Output ────────────────────────────────────────────────────────
        'outtmpl': '%(title)s [%(id)s].%(ext)s',
        'restrictfilenames': False,  # keep spaces instead of turning them into underscores

        # ── Post-processing ───────────────────────────────────────────────
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
        ],

        # ── Reliability ───────────────────────────────────────────────────
        'socket_timeout': 30,
        'ignoreerrors': False,
        'quiet': False,
        'no_warnings': False,
    }

    print("Downloading highest available quality…")
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
        print("  3. Verify the URL is correct and the content is publicly available.")
        print("  4. For YouTube specifically, make sure Deno is installed (see note above).")
        return False


if __name__ == "__main__":
    print("=== Universal Video Downloader ===")
    video_url = input("\nEnter the video URL (any supported site): ").strip()
    print()
    success = download_video(video_url)
    print("-" * 40)
    if success:
        print("Thank you for using the Video Downloader!")
    else:
        print("Download failed. Please try again.")
