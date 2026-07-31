import customtkinter
from yt_dlp import YoutubeDL
import threading
import re
from PIL import Image
import requests
from io import BytesIO
import os
import sys
import tempfile
import subprocess
from tkinter import filedialog

# ── Suppress console on frozen Windows builds ─────────────────────────────────
if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    import ctypes
    hWnd = ctypes.WinDLL('kernel32', use_last_error=True).GetConsoleWindow()
    if hWnd:
        ctypes.WinDLL('user32', use_last_error=True).ShowWindow(hWnd, 0)

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
            with YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}) as ydl:
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
        quality = self.audio_combo.get().split()[0]   # "192 kbps" → "192"
        self._lock()
        self.opts_frame.grid_remove()
        self._clear_opts()
        self._init_progress()
        self._status(f"Downloading MP3 at {quality} kbps…", self.C_MUTED)
        threading.Thread(target=self._audio_thread, args=(quality,), daemon=True).start()

    def _start_video(self):
        import shutil
        # ffmpeg is mandatory: YouTube serves 720p+ as separate video-only and
        # audio-only streams that must be merged. Detect it early so the user
        # gets an actionable message instead of a silent 360p fallback.
        if not shutil.which('ffmpeg'):
            self._status(
                "ffmpeg not found — it is required to merge the separate video "
                "and audio streams that YouTube uses for 720p and above.\n"
                "Install ffmpeg from https://ffmpeg.org and ensure it is in your PATH.",
                self.C_ERROR,
            )
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

    # ═══════════════════════════════════════════════════════ MAIN ════════════

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    YouTubeDownloader().run()
