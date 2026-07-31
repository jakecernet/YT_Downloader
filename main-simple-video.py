import os
import platform
import shutil
import subprocess
from yt_dlp import YoutubeDL

JS_RUNTIMES = ('deno', 'node', 'bun', 'quickjs')


def _deno_bin_dir() -> str:
    """Directory Deno's official installer places the binary in."""
    if platform.system() == 'Windows':
        return os.path.join(os.environ.get('USERPROFILE', ''), '.deno', 'bin')
    return os.path.join(os.path.expanduser('~'), '.deno', 'bin')


def _install_deno() -> bool:
    """Run Deno's official installer script for the current OS."""
    system = platform.system()
    try:
        if system == 'Windows':
            cmd = ['powershell', '-NoProfile', '-Command',
                   'irm https://deno.land/install.ps1 | iex']
        else:
            cmd = ['sh', '-c', 'curl -fsSL https://deno.land/install.sh | sh']

        print("Installing Deno…")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"Deno installer exited with an error:\n{result.stderr.strip()}")
            return False
    except Exception as exc:
        print(f"Could not run the Deno installer automatically: {exc}")
        return False

    bin_dir = _deno_bin_dir()
    exe = 'deno.exe' if system == 'Windows' else 'deno'
    if os.path.exists(os.path.join(bin_dir, exe)):
        # Make it usable immediately for the rest of this run.
        os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
        return True
    return False


def check_requirements() -> bool:
    """Verify ffmpeg (required) and ensure a JS runtime is available for YouTube."""
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
    if not any(shutil.which(rt) for rt in JS_RUNTIMES):
        print(
            "No supported JavaScript runtime (deno, node, bun, or quickjs) was found on your PATH.\n"
            "YouTube now requires one of these to fetch some/all formats (other sites are unaffected)."
        )
        answer = input("Install Deno automatically now? [Y/n]: ").strip().lower()
        if answer in ('', 'y', 'yes'):
            if _install_deno():
                print("Deno installed successfully.\n")
            else:
                print(
                    "Automatic install didn't succeed. You can install manually from:\n"
                    "  https://docs.deno.com/runtime/getting_started/installation/\n"
                    "YouTube downloads may fail or be limited without it; other sites will still work.\n"
                )
        else:
            print(
                "Skipping install — YouTube downloads may fail or be limited.\n"
                "Install manually anytime from: https://docs.deno.com/runtime/getting_started/installation/\n"
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

    if platform.system() == 'Windows':
        try:
            import msvcrt
            print("\nPress any key to exit...")
            msvcrt.getch()
        except Exception:
            input("\nPress Enter to exit...")
    else:
        input("\nPress Enter to exit...")