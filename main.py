import customtkinter
from yt_dlp import YoutubeDL
import threading
from PIL import Image
import requests
from io import BytesIO
import os
import sys
import re
import time
import shutil
import platform
import tempfile
import subprocess
import importlib
import importlib.metadata
from tkinter import filedialog

# ── Suppress console on frozen Windows builds ─────────────────────────────────
if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    import ctypes
    hWnd = ctypes.WinDLL('kernel32', use_last_error=True).GetConsoleWindow()
    if hWnd:
        ctypes.WinDLL('user32', use_last_error=True).ShowWindow(hWnd, 0)

# ── Tool locations / helpers ──────────────────────────────────────────────────
FROZEN           = getattr(sys, 'frozen', False)
JS_RUNTIMES      = ('deno', 'node', 'bun', 'quickjs')
CONFIG_DIR       = os.path.join(os.path.expanduser('~'), '.ytdl-gui')
FFMPEG_PATH_FILE = os.path.join(CONFIG_DIR, 'ffmpeg_dir.txt')
DENO_BIN         = os.path.join(os.path.expanduser('~'), '.deno', 'bin')
_NOWIN           = {'creationflags': 0x08000000} if sys.platform == 'win32' else {}


def _prepend_path(d):
    if d and os.path.isdir(d) and d not in os.environ.get('PATH', '').split(os.pathsep):
        os.environ['PATH'] = d + os.pathsep + os.environ.get('PATH', '')


def _bootstrap_path():
    """Make previously installed Deno / ffmpeg visible to this process."""
    _prepend_path(DENO_BIN)
    try:
        with open(FFMPEG_PATH_FILE, encoding='utf-8') as f:
            _prepend_path(f.read().strip())
    except OSError:
        pass


def _js_opts():
    """yt-dlp options that enable a JS runtime + the YouTube challenge solver."""
    opts = {'remote_components': ['ejs:github']}
    rt = next((r for r in JS_RUNTIMES if shutil.which(r)), None)
    if rt:
        opts['js_runtimes'] = {rt: {}}
    return opts


_bootstrap_path()

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")


class YouTubeDownloader:
    # ── Colour palette ────────────────────────────────────────────────────────
    C_GREEN   = "#1DB954";  C_GREEN_H  = "#17a049"
    C_RED     = "#E53935";  C_RED_H    = "#c62828"
    C_MUTED   = "#888888"
    C_SUCCESS = "#50C878"
    C_ERROR   = "#FF5555"
    C_LINK    = "#6BA3D6"
    C_WARN    = "#E6B800"

    def __init__(self):
        self.app = customtkinter.CTk()
        self.app.title("YouTube Downloader")
        self.app.geometry("960x760")
        self.app.resizable(False, False)

        self.video_info      = None
        self.thumbnail_path  = None
        self.dynamic_widgets = []   # widgets owned by the current option strip
        self.progress_bar    = None
        self.progress_label  = None
        self.download_dir    = os.path.join(os.path.expanduser("~"), "Downloads")
        self.tool_win        = None
        self.tool_rows       = {}
        self.tool_busy       = False
        self.restart_btn     = None
        self._warn_shown     = False

        self._build_ui()

    # ═══════════════════════════════════════════════════════ UI CONSTRUCTION ══

    def _build_ui(self):
        self.app.columnconfigure(0, weight=1)

        # ── Row 0: Header ─────────────────────────────────────────────────────
        hdr = customtkinter.CTkFrame(self.app, fg_color="transparent")
        hdr.grid(row=0, column=0, pady=(18, 4))
        customtkinter.CTkLabel(
            hdr, text="YouTube Downloader",
            font=customtkinter.CTkFont(size=26, weight="bold")
        ).pack()
        customtkinter.CTkLabel(
            hdr, text="powered by yt-dlp",
            font=customtkinter.CTkFont(size=11), text_color=self.C_MUTED
        ).pack()

        # ── Row 1: URL bar ────────────────────────────────────────────────────
        url_row = customtkinter.CTkFrame(self.app, fg_color="transparent")
        url_row.grid(row=1, column=0, pady=10)

        self.url_entry = customtkinter.CTkEntry(
            url_row, placeholder_text="Paste a YouTube URL here…",
            width=680, height=42, font=customtkinter.CTkFont(size=14), corner_radius=8
        )
        self.url_entry.pack(side="left", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _: self.fetch_video_info())

        self.info_btn = customtkinter.CTkButton(
            url_row, text="Get Info", command=self.fetch_video_info,
            width=120, height=42,
            font=customtkinter.CTkFont(size=14, weight="bold"), corner_radius=8
        )
        self.info_btn.pack(side="left")

        # ── Row 2: Save-to row ────────────────────────────────────────────────
        dir_row = customtkinter.CTkFrame(self.app, fg_color="transparent")
        dir_row.grid(row=2, column=0, pady=(0, 6))

        customtkinter.CTkLabel(
            dir_row, text="Save to:",
            font=customtkinter.CTkFont(size=12), text_color=self.C_MUTED
        ).pack(side="left", padx=(0, 4))

        self.dir_lbl = customtkinter.CTkLabel(
            dir_row, text=self._fmt_path(self.download_dir),
            font=customtkinter.CTkFont(size=12),
            text_color=self.C_LINK, cursor="hand2"
        )
        self.dir_lbl.pack(side="left")
        self.dir_lbl.bind("<Button-1>", lambda _: self._browse())

        customtkinter.CTkButton(
            dir_row, text="Browse…", command=self._browse,
            width=74, height=26,
            font=customtkinter.CTkFont(size=12), corner_radius=6
        ).pack(side="left", padx=8)

        # ── Row 3: Video info panel ───────────────────────────────────────────
        self.info_panel = customtkinter.CTkFrame(
            self.app, width=900, height=220, corner_radius=12
        )
        self.info_panel.grid(row=3, column=0, padx=30, pady=8)
        self.info_panel.pack_propagate(False)

        customtkinter.CTkLabel(
            self.info_panel,
            text="Enter a YouTube URL and press  Get Info  to start",
            font=customtkinter.CTkFont(size=13), text_color=self.C_MUTED
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Row 4: Format chooser (hidden until video is loaded) ──────────────
        self.fmt_frame = customtkinter.CTkFrame(self.app, fg_color="transparent")
        self.fmt_frame.grid(row=4, column=0, pady=10)
        self.fmt_frame.grid_remove()

        customtkinter.CTkLabel(
            self.fmt_frame, text="Download as:",
            font=customtkinter.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=16)

        self.audio_btn = customtkinter.CTkButton(
            self.fmt_frame, text="🎵  Audio (MP3)",
            command=self._show_audio_opts,
            width=155, height=42,
            font=customtkinter.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=self.C_GREEN, hover_color=self.C_GREEN_H
        )
        self.audio_btn.grid(row=0, column=1, padx=8)

        self.video_btn = customtkinter.CTkButton(
            self.fmt_frame, text="🎬  Video (MP4)",
            command=self._show_video_opts,
            width=155, height=42,
            font=customtkinter.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=self.C_RED, hover_color=self.C_RED_H
        )
        self.video_btn.grid(row=0, column=2, padx=8)

        # ── Row 5: Quality / options strip (hidden until format chosen) ────────
        self.opts_frame = customtkinter.CTkFrame(
            self.app, width=900, height=78, corner_radius=12
        )
        self.opts_frame.grid(row=5, column=0, padx=30, pady=4)
        self.opts_frame.pack_propagate(False)
        self.opts_frame.grid_remove()

        # ── Row 6: Progress strip (hidden until download starts) ──────────────
        self.prog_frame = customtkinter.CTkFrame(
            self.app, width=900, height=90, corner_radius=12
        )
        self.prog_frame.grid(row=6, column=0, padx=30, pady=4)
        self.prog_frame.pack_propagate(False)
        self.prog_frame.grid_remove()

        # ── Row 7: Status bar (always visible) ────────────────────────────────
        self.status_bar = customtkinter.CTkFrame(
            self.app, fg_color="transparent", height=60
        )
        self.status_bar.grid(row=7, column=0, padx=30, pady=(4, 14))
        self.status_bar.pack_propagate(False)

        # ── Tools button (top-right) ──────────────────────────────────────────
        customtkinter.CTkButton(
            self.app, text="⚙  Tools", command=self._open_tools,
            width=90, height=30, corner_radius=8,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color="#333333", hover_color="#444444"
        ).place(relx=1.0, x=-18, y=16, anchor="ne")

        self.app.after(400, self._startup_check)

    # ═══════════════════════════════════════════════════════ HELPERS ══════════

    @staticmethod
    def _fmt_path(p, n=65):
        return p if len(p) <= n else "…" + p[-(n - 1):]

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.download_dir)
        if d:
            self.download_dir = d
            self.dir_lbl.configure(text=self._fmt_path(d))

    def _open_dir(self):
        if sys.platform == 'win32':
            os.startfile(self.download_dir)
        elif sys.platform == 'darwin':
            subprocess.run(['open', self.download_dir])
        else:
            subprocess.run(['xdg-open', self.download_dir])

    def _clear_opts(self):
        """Destroy widgets owned by the current option strip."""
        for w in self.dynamic_widgets:
            w.destroy()
        self.dynamic_widgets.clear()

    def _lock(self):
        self.audio_btn.configure(state="disabled")
        self.video_btn.configure(state="disabled")
        self.info_btn.configure(state="disabled")

    def _unlock(self):
        self.audio_btn.configure(state="normal")
        self.video_btn.configure(state="normal")
        self.info_btn.configure(state="normal")

    def _validate_url(self, url):
        if not url or not url.strip():
            return False, "Please enter a URL."
        return True, ""

    # ═══════════════════════════════════════════════════════ STATUS ═══════════

    def _status(self, msg, color=None):
        for w in self.status_bar.winfo_children():
            w.destroy()
        if msg:
            customtkinter.CTkLabel(
                self.status_bar, text=msg,
                font=customtkinter.CTkFont(size=13),
                text_color=color or "#CCCCCC",
                wraplength=860
            ).pack(expand=True)

    def _status_success(self, title, height=None):
        """Status row with success message + optional resolution + Open Folder button."""
        for w in self.status_bar.winfo_children():
            w.destroy()
        row = customtkinter.CTkFrame(self.status_bar, fg_color="transparent")
        row.pack(expand=True, fill="both")
        short  = (title[:48] + "…") if len(title) > 48 else title
        badge  = f"  [{height}p]" if height else ""
        customtkinter.CTkLabel(
            row, text=f"✓  {short}{badge}",
            font=customtkinter.CTkFont(size=13), text_color=self.C_SUCCESS
        ).pack(side="left", pady=10)
        customtkinter.CTkButton(
            row, text="Open Folder", command=self._open_dir,
            width=110, height=28,
            font=customtkinter.CTkFont(size=12), corner_radius=6
        ).pack(side="right", padx=(8, 0), pady=10)

    # ═══════════════════════════════════════════════════════ PROGRESS ═════════

    def _init_progress(self):
        for w in self.prog_frame.winfo_children():
            w.destroy()
        self.prog_frame.grid()

        self.progress_bar = customtkinter.CTkProgressBar(
            self.prog_frame, width=840, height=14,
            corner_radius=7, mode="determinate"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(18, 5), padx=30)

        self.progress_label = customtkinter.CTkLabel(
            self.prog_frame, text="Preparing…",
            font=customtkinter.CTkFont(size=12), text_color=self.C_MUTED
        )
        self.progress_label.pack()

    def _on_progress(self, d):
        """yt-dlp progress hook — called from the download thread."""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            done  = d.get('downloaded_bytes', 0)
            speed = d.get('speed') or 0
            eta   = d.get('eta') or 0

            frac = min(done / total, 1.0) if total else 0

            spd = (f"{speed / 1_048_576:.1f} MB/s" if speed >= 1_048_576
                   else f"{speed / 1024:.0f} KB/s"   if speed >= 1024
                   else f"{speed:.0f} B/s"            if speed else "—")

            eta_s = (f"{eta // 60}m {eta % 60:02d}s" if eta >= 60
                     else f"{eta}s"                   if eta else "—")

            pct  = d.get('_percent_str', '').strip()
            text = f"{pct}  ·  {spd}  ·  ETA {eta_s}"

            self.app.after(0, self.progress_bar.set, frac)
            self.app.after(0, lambda t=text: self.progress_label.configure(text=t))

        elif d['status'] == 'finished':
            self.app.after(0, self.progress_bar.set, 1.0)
            self.app.after(0, lambda: self.progress_label.configure(text="Post-processing…"))

    # ═══════════════════════════════════════════════════════ FETCH INFO ════════

    def fetch_video_info(self):
        ok, msg = self._validate_url(self.url_entry.get())
        if not ok:
            self._status(msg, self.C_ERROR)
            return
        self.info_btn.configure(state="disabled", text="Loading…")
        self._status("Fetching video information…", self.C_MUTED)
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        try:
            url = self.url_entry.get().strip()
            with YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True, **_js_opts()}) as ydl:
                info = ydl.extract_info(url, download=False)
            self.video_info = info

            thumb = info.get('thumbnail')
            if thumb:
                r = requests.get(thumb, timeout=10)
                img = Image.open(BytesIO(r.content))
                img.thumbnail((298, 188), Image.Resampling.LANCZOS)
                self.thumbnail_path = os.path.join(tempfile.gettempdir(), 'yt_thumb.jpg')
                img.save(self.thumbnail_path)

            self.app.after(0, self._render_info)
        except Exception as exc:
            self.app.after(0, self._status, f"Could not fetch info: {exc}", self.C_ERROR)
            self.app.after(0, lambda: self.info_btn.configure(state="normal", text="Get Info"))

    def _render_info(self):
        for w in self.info_panel.winfo_children():
            w.destroy()
        self._status("")

        if not self.video_info:
            return
        info = self.video_info

        # Left: thumbnail ──────────────────────────────────────────────────────
        left = customtkinter.CTkFrame(self.info_panel, fg_color="transparent")
        left.pack(side="left", padx=(14, 8), pady=14)

        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            img = customtkinter.CTkImage(
                Image.open(self.thumbnail_path),
                Image.open(self.thumbnail_path),
                size=(298, 188)
            )
            thumb_lbl = customtkinter.CTkLabel(left, image=img, text="", corner_radius=6)
            thumb_lbl.image = img   # keep reference
            thumb_lbl.pack()

        # Right: metadata ──────────────────────────────────────────────────────
        right = customtkinter.CTkFrame(self.info_panel, fg_color="transparent")
        right.pack(side="left", padx=(6, 14), pady=14, fill="both", expand=True)

        title = info.get('title', 'Unknown')
        customtkinter.CTkLabel(
            right,
            text=(title[:68] + "…") if len(title) > 68 else title,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            anchor="w", wraplength=510
        ).pack(anchor="w", pady=(4, 10))

        dur = info.get('duration') or 0
        h, m, s = dur // 3600, (dur % 3600) // 60, dur % 60
        dur_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

        vc = info.get('view_count') or 0
        views = (f"{vc / 1_000_000:.1f}M" if vc >= 1_000_000
                 else f"{vc / 1000:.1f}K"  if vc >= 1000
                 else str(vc))

        # `get('upload_date', '')` returns None when the key exists but is None,
        # so we use `or ''` to safely coerce None → empty string.
        # Fall back to release_date if upload_date is absent.
        ud = info.get('upload_date') or info.get('release_date') or ''
        date_str = f"{ud[:4]}-{ud[4:6]}-{ud[6:]}" if len(ud) == 8 else "—"

        for label, value in [
            ("📺  Channel",  info.get('uploader', '—')),
            ("⏱  Duration", dur_str),
            ("👁  Views",    f"{views} views"),
            ("📅  Uploaded", date_str),
        ]:
            r = customtkinter.CTkFrame(right, fg_color="transparent")
            r.pack(anchor="w", pady=3)
            customtkinter.CTkLabel(
                r, text=label + ":",
                font=customtkinter.CTkFont(size=12, weight="bold"),
                text_color=self.C_MUTED, width=100, anchor="w"
            ).pack(side="left")
            customtkinter.CTkLabel(
                r, text=value,
                font=customtkinter.CTkFont(size=12), anchor="w"
            ).pack(side="left", padx=4)

        self.fmt_frame.grid()
        self.info_btn.configure(state="normal", text="Get Info")

    # ═══════════════════════════════════════════════════════ FORMAT OPTIONS ════

    def _show_audio_opts(self):
        self._clear_opts()
        self.prog_frame.grid_remove()
        self.opts_frame.grid()

        # Centre the controls inside the strip
        inner = customtkinter.CTkFrame(self.opts_frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self.dynamic_widgets.append(inner)   # destroying inner destroys children too

        customtkinter.CTkLabel(
            inner, text="Quality:",
            font=customtkinter.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 8))

        self.audio_combo = customtkinter.CTkComboBox(
            inner, values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
            width=152, height=36, font=customtkinter.CTkFont(size=13), state="readonly"
        )
        self.audio_combo.set("192 kbps")
        self.audio_combo.pack(side="left", padx=8)

        customtkinter.CTkButton(
            inner, text="⬇  Download", command=self._start_audio,
            width=140, height=36,
            font=customtkinter.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=self.C_GREEN, hover_color=self.C_GREEN_H
        ).pack(side="left", padx=8)

    def _show_video_opts(self):
        self._clear_opts()
        self.prog_frame.grid_remove()
        self.opts_frame.grid()

        inner = customtkinter.CTkFrame(self.opts_frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self.dynamic_widgets.append(inner)

        customtkinter.CTkLabel(
            inner, text="Resolution:",
            font=customtkinter.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 8))

        self.video_combo = customtkinter.CTkComboBox(
            inner, values=["360p", "480p", "720p", "1080p", "1440p", "2160p (4K)"],
            width=152, height=36, font=customtkinter.CTkFont(size=13), state="readonly"
        )
        self.video_combo.set("1080p")
        self.video_combo.pack(side="left", padx=8)

        customtkinter.CTkButton(
            inner, text="⬇  Download", command=self._start_video,
            width=140, height=36,
            font=customtkinter.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=self.C_RED, hover_color=self.C_RED_H
        ).pack(side="left", padx=8)

    # ═══════════════════════════════════════════════════════ DOWNLOAD ═════════

    def _start_audio(self):
        if not self._require_ffmpeg():
            return
        quality = self.audio_combo.get().split()[0]   # "192 kbps" → "192"
        self._lock()
        self.opts_frame.grid_remove()
        self._clear_opts()
        self._init_progress()
        self._status(f"Downloading MP3 at {quality} kbps…", self.C_MUTED)
        threading.Thread(target=self._audio_thread, args=(quality,), daemon=True).start()

    def _start_video(self):
        if not self._require_ffmpeg():
            return

        quality_str = self.video_combo.get()
        quality     = quality_str.split('p')[0]   # "1080p" -> "1080", "2160p (4K)" -> "2160"
        self._lock()
        self.opts_frame.grid_remove()
        self._clear_opts()
        self._init_progress()
        self._status(f"Downloading MP4 at {quality_str}\u2026", self.C_MUTED)
        threading.Thread(target=self._video_thread, args=(quality,), daemon=True).start()

    def _audio_thread(self, quality):
        url     = self.url_entry.get().strip()
        outtmpl = os.path.join(self.download_dir, '%(title)s [%(id)s].%(ext)s')
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            with YoutubeDL({
                'format':        'bestaudio/best',
                'outtmpl':       outtmpl,
                'writethumbnail': True,
                'postprocessors': [
                    # 1. Extract and re-encode audio to MP3 at chosen bitrate
                    {'key': 'FFmpegExtractAudio',
                     'preferredcodec': 'mp3', 'preferredquality': quality},
                    # 2. Write ID3 / metadata tags
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                    # 3. Embed thumbnail as album art (requires mutagen)
                    {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
                ],
                'quiet':          True,
                'no_warnings':    True,
                'progress_hooks': [self._on_progress],
                **_js_opts(),
            }) as ydl:
                info = ydl.extract_info(url, download=True)
            self.app.after(0, self._on_done, info.get('title', 'Unknown'))
        except Exception as exc:
            self.app.after(0, self._on_error, str(exc))

    def _video_thread(self, quality):
        url     = self.url_entry.get().strip()
        outtmpl = os.path.join(self.download_dir, '%(title)s [%(id)s].%(ext)s')
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            with YoutubeDL({
                # [acodec=none] selects video-ONLY streams (no embedded audio).
                # [vcodec=none] selects audio-ONLY streams (no embedded video).
                # Together they explicitly exclude YouTube's pre-merged combined
                # streams, which top out at ~480p. ffmpeg (confirmed present by
                # _start_video) merges the two streams into a single mp4.
                #
                # The fallback after '/' drops the height cap: if the video has
                # no stream at the requested height (e.g. a 720p-max upload
                # selected at 1080p) we still get the best available quality
                # rather than an error or a silent 360p combined fallback.
                'format': (
                    f'bestvideo[acodec=none][height<={quality}]'
                    f'+bestaudio[vcodec=none]'
                    f'/bestvideo[acodec=none]+bestaudio[vcodec=none]'
                ),
                'merge_output_format': 'mp4',
                'outtmpl':        outtmpl,
                'writethumbnail': True,
                'postprocessors': [
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                    {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
                ],
                'quiet':          True,
                'no_warnings':    True,
                'progress_hooks': [self._on_progress],
                **_js_opts(),
            }) as ydl:
                info = ydl.extract_info(url, download=True)
            actual = self._actual_height(info)
            title  = info.get('title', 'Unknown')
            self.app.after(0, self._on_done, title, actual)
        except Exception as exc:
            self.app.after(0, self._on_error, str(exc))

    @staticmethod
    def _actual_height(info):
        """Return the video height that was actually downloaded, or None."""
        for fmt in (info.get('requested_formats') or []):
            if fmt.get('vcodec') not in (None, 'none'):
                return fmt.get('height')
        return info.get('height')

    def _on_done(self, title, height=None):
        self.prog_frame.grid_remove()
        self._status_success(title, height)
        self._unlock()

    def _on_error(self, msg):
        self.prog_frame.grid_remove()
        self._status(f"Download failed: {msg}", self.C_ERROR)
        self._unlock()

    # ═══════════════════════════════════════════════════════ TOOLS ════════════
    # yt-dlp / Deno / ffmpeg: status, install, update — each with a progress bar.

    TOOLS = (
        ("ytdlp",  "yt-dlp", "Download engine"),
        ("deno",   "Deno",   "JavaScript runtime — needed for YouTube"),
        ("ffmpeg", "ffmpeg", "Merges video + audio and converts to MP3"),
    )

    def _ui(self, fn, *a):
        """Run fn(*a) on the Tk thread (safe to call from worker threads)."""
        try:
            self.app.after(0, lambda: fn(*a))
        except Exception:
            pass

    def _row(self, key):
        try:
            if self.tool_win is None or not self.tool_win.winfo_exists():
                return None
            return self.tool_rows.get(key)
        except Exception:
            return None

    def _startup_check(self):
        missing = []
        if not shutil.which('ffmpeg'):
            missing.append("ffmpeg")
        if not any(shutil.which(r) for r in JS_RUNTIMES):
            missing.append("a JavaScript runtime (Deno)")
        if missing:
            self._warn_shown = True
            self._status(f"⚠  Missing: {' and '.join(missing)} — open  ⚙ Tools  to install.",
                         self.C_WARN)
        elif self._warn_shown:
            self._warn_shown = False
            self._status("")

    def _require_ffmpeg(self):
        if shutil.which('ffmpeg'):
            return True
        self._status("ffmpeg not found — install it from the Tools window.", self.C_ERROR)
        self._open_tools()
        return False

    # ── Tools window ──────────────────────────────────────────────────────────

    def _open_tools(self):
        if self.tool_win is not None and self.tool_win.winfo_exists():
            self.tool_win.lift()
            self.tool_win.focus()
            return

        win = customtkinter.CTkToplevel(self.app)
        win.title("Tools")
        win.geometry("700x500")
        win.resizable(False, False)
        win.transient(self.app)
        self.tool_win = win

        customtkinter.CTkLabel(
            win, text="Tools & dependencies",
            font=customtkinter.CTkFont(size=18, weight="bold")
        ).pack(pady=(16, 2))
        customtkinter.CTkLabel(
            win, text="Install or update what the downloader needs",
            font=customtkinter.CTkFont(size=12), text_color=self.C_MUTED
        ).pack(pady=(0, 8))

        self.tool_rows = {}
        for key, name, desc in self.TOOLS:
            card = customtkinter.CTkFrame(win, corner_radius=10)
            card.pack(fill="x", padx=20, pady=6)

            top = customtkinter.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(10, 2))

            left = customtkinter.CTkFrame(top, fg_color="transparent")
            left.pack(side="left")
            customtkinter.CTkLabel(
                left, text=name, anchor="w",
                font=customtkinter.CTkFont(size=14, weight="bold")
            ).pack(anchor="w")
            status = customtkinter.CTkLabel(
                left, text="Checking…", anchor="w",
                font=customtkinter.CTkFont(size=12), text_color=self.C_MUTED
            )
            status.pack(anchor="w")

            btn = customtkinter.CTkButton(
                top, text="…", width=120, height=32, state="disabled",
                font=customtkinter.CTkFont(size=13, weight="bold"), corner_radius=8,
                command=lambda k=key: self._tool_action(k)
            )
            btn.pack(side="right")

            bar = customtkinter.CTkProgressBar(card, width=630, height=10,
                                               corner_radius=5, mode="determinate")
            bar.set(0)
            bar.pack(padx=14, pady=(6, 2))

            detail = customtkinter.CTkLabel(
                card, text=desc, wraplength=620,
                font=customtkinter.CTkFont(size=11), text_color=self.C_MUTED
            )
            detail.pack(pady=(0, 10))

            self.tool_rows[key] = {'status': status, 'btn': btn, 'bar': bar, 'detail': detail}

        self.restart_btn = customtkinter.CTkButton(
            win, text="↻  Restart app to use the new yt-dlp",
            command=self._restart, height=34, corner_radius=8,
            fg_color=self.C_GREEN, hover_color=self.C_GREEN_H,
            font=customtkinter.CTkFont(size=13, weight="bold")
        )  # packed only when a restart is needed

        win.after(150, win.focus)
        self._refresh_tools()

    def _restart(self):
        args = [sys.executable] + (sys.argv[1:] if FROZEN else sys.argv)
        subprocess.Popen(args)
        self.app.destroy()
        sys.exit(0)

    # ── Status probing ────────────────────────────────────────────────────────

    def _refresh_tools(self):
        threading.Thread(target=self._refresh_thread, daemon=True).start()

    def _refresh_thread(self):
        for key in ("ytdlp", "deno", "ffmpeg"):
            try:
                installed, latest = getattr(self, f"_probe_{key}")()
            except Exception:
                installed, latest = None, None
            self._ui(self._apply_probe, key, installed, latest)

    @staticmethod
    def _running_ytdlp():
        from yt_dlp.version import __version__
        return __version__

    def _probe_ytdlp(self):
        try:
            installed = importlib.metadata.version('yt-dlp')
        except Exception:
            installed = self._running_ytdlp()
        latest = None
        try:
            latest = requests.get("https://pypi.org/pypi/yt-dlp/json",
                                  timeout=8).json()["info"]["version"]
        except Exception:
            pass
        return installed, latest

    def _probe_deno(self):
        exe = shutil.which('deno')
        if not exe:
            return None, None
        out = subprocess.run([exe, '--version'], capture_output=True, text=True,
                             timeout=10, **_NOWIN).stdout
        m = re.search(r'deno (\S+)', out)
        installed = m.group(1) if m else "unknown"
        latest = None
        try:
            latest = requests.get("https://api.github.com/repos/denoland/deno/releases/latest",
                                  timeout=8).json()["tag_name"].lstrip('v')
        except Exception:
            pass
        return installed, latest

    def _probe_ffmpeg(self):
        exe = shutil.which('ffmpeg')
        if not exe:
            return None, None
        out = subprocess.run([exe, '-version'], capture_output=True, text=True,
                             timeout=10, **_NOWIN).stdout
        m = re.search(r'ffmpeg version (\S+)', out)
        return (m.group(1) if m else "unknown"), None

    def _apply_probe(self, key, installed, latest):
        row = self._row(key)
        if not row:
            return
        norm = lambda v: (v or '').lstrip('v')
        if installed is None:
            text, color, btn, ok = "Not installed", self.C_ERROR, "Install", True
        elif latest and norm(latest) != norm(installed):
            text, color, btn, ok = (f"v{installed}  ·  update available (v{norm(latest)})",
                                    self.C_WARN, "Update", True)
        elif latest:
            text, color, btn, ok = f"v{installed}  ·  up to date", self.C_SUCCESS, "Up to date", False
        elif key == 'ffmpeg':
            text, color, btn, ok = f"v{installed}  ·  installed", self.C_SUCCESS, "Installed", False
        else:
            text, color, btn, ok = f"v{installed}", self.C_SUCCESS, "Update", True

        if key == 'ytdlp' and installed and installed != self._running_ytdlp():
            text += "  ·  restart needed"
            self.restart_btn.pack(pady=(6, 10))

        row['status'].configure(text=text, text_color=color)
        row['btn'].configure(text=btn, state="normal" if (ok and not self.tool_busy) else "disabled")

    # ── Install / update plumbing ─────────────────────────────────────────────

    def _tool_prog(self, key, frac=None, text="", color=None):
        """frac=None → indeterminate (animated) bar; otherwise 0..1."""
        def apply():
            row = self._row(key)
            if not row:
                return
            bar = row['bar']
            if frac is None:
                if bar.cget('mode') != 'indeterminate':
                    bar.configure(mode='indeterminate')
                    bar.start()
            else:
                if bar.cget('mode') != 'determinate':
                    bar.stop()
                    bar.configure(mode='determinate')
                bar.set(max(0.0, min(frac, 1.0)))
            row['detail'].configure(text=text, text_color=color or self.C_MUTED)
        self._ui(apply)

    def _tool_action(self, key):
        if self.tool_busy:
            return
        self.tool_busy = True
        for r in self.tool_rows.values():
            r['btn'].configure(state="disabled")
        self._tool_prog(key, 0.0, "Starting…")
        threading.Thread(target=self._install_thread, args=(key,), daemon=True).start()

    def _install_thread(self, key):
        try:
            getattr(self, f"_install_{key}")()
            self._tool_prog(key, 1.0, "Done ✓", self.C_SUCCESS)
        except Exception as exc:
            self._tool_prog(key, 0.0, f"Failed: {exc}", self.C_ERROR)
        finally:
            self.tool_busy = False
            _bootstrap_path()
            self._ui(self._after_install)

    def _after_install(self):
        self._startup_check()
        if self.tool_win is not None:
            self._refresh_tools()

    def _pip_install(self, key, package, lo=0.0, hi=1.0):
        """pip install --upgrade <package>, mapping pip's output to bar progress."""
        if FROZEN:
            raise RuntimeError("not available in the packaged app — install a newer build instead")
        stages = (('Collecting', .15), ('Requirement already', .3), ('Downloading', .4),
                  ('Installing collected', .8), ('Successfully', 1.0))
        base = [sys.executable, '-m', 'pip', 'install', '--upgrade', package,
                '--progress-bar', 'off', '--disable-pip-version-check']
        out = []
        for extra in ([], ['--user', '--break-system-packages']):
            frac = 0.05
            self._tool_prog(key, lo + (hi - lo) * frac, "Starting pip…")
            proc = subprocess.Popen(base + extra, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1,
                                    encoding='utf-8', errors='replace', **_NOWIN)
            out = []
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                out.append(line)
                for prefix, f in stages:
                    if line.startswith(prefix):
                        frac = max(frac, f)
                        break
                self._tool_prog(key, lo + (hi - lo) * frac, line[:90])
            if proc.wait() == 0:
                return
            if 'externally-managed' not in '\n'.join(out):
                break
        raise RuntimeError(out[-1] if out else "pip failed")

    # ── yt-dlp ────────────────────────────────────────────────────────────────

    def _install_ytdlp(self):
        self._pip_install('ytdlp', 'yt-dlp[default]')

    # ── Deno (direct download → real byte progress) ───────────────────────────

    @staticmethod
    def _deno_target():
        arm = platform.machine().lower() in ('arm64', 'aarch64')
        if sys.platform == 'win32':
            return 'x86_64-pc-windows-msvc'
        if sys.platform == 'darwin':
            return 'aarch64-apple-darwin' if arm else 'x86_64-apple-darwin'
        return 'aarch64-unknown-linux-gnu' if arm else 'x86_64-unknown-linux-gnu'

    def _install_deno(self):
        import zipfile
        url = ("https://github.com/denoland/deno/releases/latest/download/"
               f"deno-{self._deno_target()}.zip")
        os.makedirs(DENO_BIN, exist_ok=True)
        tmp = os.path.join(tempfile.gettempdir(), 'deno_download.zip')
        self._tool_prog('deno', 0.0, "Connecting…")
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get('Content-Length', 0))
                done, t0 = 0, time.time()
                with open(tmp, 'wb') as f:
                    for chunk in r.iter_content(65536):
                        f.write(chunk)
                        done += len(chunk)
                        speed = done / max(time.time() - t0, 1e-6) / 1_048_576
                        txt = (f"{done / 1_048_576:.1f}"
                               + (f" / {total / 1_048_576:.1f}" if total else "")
                               + f" MB  ·  {speed:.1f} MB/s")
                        self._tool_prog('deno', (done / total * 0.9) if total else None, txt)
            self._tool_prog('deno', 0.95, "Extracting…")
            with zipfile.ZipFile(tmp) as z:
                z.extractall(DENO_BIN)
            if sys.platform != 'win32':
                os.chmod(os.path.join(DENO_BIN, 'deno'), 0o755)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        _bootstrap_path()
        if not shutil.which('deno'):
            raise RuntimeError("install finished but deno was not found")

    # ── ffmpeg (static build via the static-ffmpeg package) ───────────────────

    def _install_ffmpeg(self):
        try:
            import static_ffmpeg
        except ImportError:
            if FROZEN:
                raise RuntimeError("not bundled in this build — install it from https://ffmpeg.org")
            self._pip_install('ffmpeg', 'static-ffmpeg', 0.0, 0.4)
            importlib.invalidate_caches()
            import static_ffmpeg
        self._tool_prog('ffmpeg', None, "Downloading ffmpeg (one-time, ~80 MB)…")
        static_ffmpeg.add_paths()   # downloads on first run, then adds to PATH
        exe = shutil.which('ffmpeg')
        if not exe:
            raise RuntimeError("download finished but ffmpeg was not found")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(FFMPEG_PATH_FILE, 'w', encoding='utf-8') as f:
            f.write(os.path.dirname(exe))   # remembered for the next launch

    # ═══════════════════════════════════════════════════════ MAIN ════════════

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    YouTubeDownloader().run()
