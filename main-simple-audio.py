import shutil
from yt_dlp import YoutubeDL


def check_requirements() -> bool:
    """Verify ffmpeg (required) and check for deno (recommended for YouTube)."""
    if not shutil.which('ffmpeg'):
        print(
            "Error: ffmpeg was not found.\n"
            "ffmpeg is required to extract/convert audio.\n"
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


def download_audio(url: str) -> bool:
    """
    Download the highest quality audio from any site yt-dlp supports.

    Output is always converted to MP3 (highest quality VBR). If the source
    has no standalone audio track (video-only), the best available video
    is downloaded first and the audio is extracted from it with ffmpeg.
    """
    if not url or not url.strip():
        print("Error: URL cannot be empty!")
        return False

    if not check_requirements():
        return False

    try:
        ydl_opts = {
            # bestaudio = highest quality standalone audio track, if one exists
            # /best     = otherwise fall back to the best combined format and
            #             let the postprocessor below pull the audio out of it
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',  # '0' = best VBR quality for mp3
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                },
            ],
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': False,  # keep spaces instead of turning them into underscores
            'writethumbnail': True,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
        }

        print("Downloading highest available audio quality…")
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Unknown')
            print(f"\n'{video_title}' downloaded successfully!")
            return True

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("\nTroubleshooting tips:")
        print("  1. Check that your internet connection is stable.")
        print("  2. Update yt-dlp:  pip install --upgrade yt-dlp")
        print("  3. Verify the URL is correct and the content is publicly available.")
        print("  4. For YouTube specifically, make sure Deno is installed (see note above).")
        return False


if __name__ == "__main__":
    print("=== Universal Audio Downloader ===")
    video_url = input("\nEnter the URL (any supported site): ").strip()
    print("\nDownloading...\n")

    if download_audio(video_url):
        print("---------------------------------")
        print("Thank you for using the Audio Downloader!")
    else:
        print("---------------------------------")
        print("Download failed. Please try again.")
