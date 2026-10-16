import os
import platform
import shutil
import subprocess
import sys
from yt_dlp import YoutubeDL

JS_RUNTIMES = ('deno', 'node', 'bun', 'quickjs')


def _deno_bin_dir() -> str:
    """Directory Deno's official installer places the binary in."""
    home = os.environ.get('USERPROFILE', '') if platform.system() == 'Windows' else os.path.expanduser('~')
    return os.path.join(home, '.deno', 'bin')


def _find_js_runtime() -> str | None:
    """Return the name of an available JS runtime, or None."""
    # Pick up a previous Deno install that isn't on PATH yet.
    bin_dir = _deno_bin_dir()
    if os.path.isdir(bin_dir) and bin_dir not in os.environ.get('PATH', ''):
        os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
    return next((rt for rt in JS_RUNTIMES if shutil.which(rt)), None)


def _install_deno() -> None:
    """Silently run Deno's official installer for the current OS."""
    if platform.system() == 'Windows':
        cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
               'irm https://deno.land/install.ps1 | iex']
    else:
        cmd = ['sh', '-c', 'curl -fsSL https://deno.land/install.sh | sh -s -- -y']
    print("Installing Deno (one-time setup)…")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                stdin=subprocess.DEVNULL)
        if result.returncode != 0:
            print(f"Deno install failed:\n{result.stderr.strip()}")
    except Exception as exc:
        print(f"Deno install failed: {exc}")


def ensure_js_runtime() -> str | None:
    """Find a JS runtime, installing Deno automatically if none exists."""
    runtime = _find_js_runtime()
    if runtime:
        return runtime
    _install_deno()
    runtime = _find_js_runtime()
    if not runtime:
        print("Could not set up a JavaScript runtime. YouTube downloads may fail; "
              "other sites will still work.\n"
              "Manual install: https://docs.deno.com/runtime/getting_started/installation/\n")
    return runtime


def _pip_install(package: str) -> bool:
    base = [sys.executable, '-m', 'pip', 'install', '--quiet', package]
    for extra in ([], ['--user', '--break-system-packages']):
        try:
            r = subprocess.run(base + extra, capture_output=True, text=True,
                               timeout=600, stdin=subprocess.DEVNULL)
            if r.returncode == 0:
                return True
        except Exception:
            pass
    return False


def ensure_ffmpeg() -> bool:
    """Make sure ffmpeg + ffprobe are available, downloading static builds if not."""
    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        return True

    print("ffmpeg not found - downloading it automatically (one-time setup)...")
    try:
        try:
            import static_ffmpeg
        except ImportError:
            if not _pip_install('static-ffmpeg'):
                raise RuntimeError("could not install the static-ffmpeg package")
            import static_ffmpeg
        static_ffmpeg.add_paths()  # downloads binaries on first run, adds them to PATH
    except Exception as exc:
        print(f"Automatic ffmpeg setup failed: {exc}")

    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        print("ffmpeg ready.\n")
        return True

    print(
        "Error: ffmpeg could not be set up automatically.\n"
        "Install it manually from https://ffmpeg.org/download.html and make sure it is in your PATH."
    )
    return False


def download_video(url: str, max_height: int | None = None) -> bool:
    """
    Download the highest quality video from any site yt-dlp supports,
    merged into a single MP4. max_height optionally caps resolution.
    """
    if not url or not url.strip():
        print("Error: URL cannot be empty.")
        return False

    if not ensure_ffmpeg():
        return False

    runtime = ensure_js_runtime()

    height_filter = f'[height<={max_height}]' if max_height else ''

    ydl_opts = {
        'format': f'bv*{height_filter}+ba/b{height_filter}',
        'merge_output_format': 'mp4',

        'outtmpl': '%(title)s.%(ext)s',
        'restrictfilenames': False,

        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
        ],

        'socket_timeout': 30,
        'ignoreerrors': False,
        'quiet': False,
        'no_warnings': False,

        # Let yt-dlp fetch its YouTube challenge solver automatically.
        'remote_components': ['ejs:github'],
    }
    # Explicitly enable whichever runtime we found (only deno is on by default).
    if runtime:
        ydl_opts['js_runtimes'] = {runtime: {}}

    print("Downloading highest available quality…")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = info.get('title', 'Unknown')

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
