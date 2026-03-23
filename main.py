import customtkinter
from yt_dlp import YoutubeDL
import threading
import re
from PIL import Image
import requests
from io import BytesIO
import os
import tempfile
import sys

# Hide console window when running as executable on Windows
if sys.platform == 'win32':
    import ctypes
    import platform

    # Only hide console if running as compiled executable (not in development)
    if getattr(sys, 'frozen', False):
        # Get the console window handle
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        user32 = ctypes.WinDLL('user32', use_last_error=True)

        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, 0)  # 0 = SW_HIDE

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")


class YouTubeDownloader:
    def __init__(self):
        self.app = customtkinter.CTk()
        self.app.title("YouTube Downloader")
        self.app.geometry("950x700")
        self.app.resizable(False, False)

        # Store widgets for cleanup
        self.dynamic_widgets = []
        self.video_info = None
        self.thumbnail_path = None

        self.setup_ui()

    def setup_ui(self):
        """Initialize the main UI components."""
        # Title
        self.title_label = customtkinter.CTkLabel(
            self.app,
            text="YouTube Downloader",
            font=customtkinter.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=15)

        # URL Entry Frame
        url_frame = customtkinter.CTkFrame(self.app, fg_color="transparent")
        url_frame.pack(pady=5)

        self.url_entry = customtkinter.CTkEntry(
            url_frame,
            placeholder_text="Enter the YouTube video URL here...",
            width=650,
            height=40,
            font=customtkinter.CTkFont(size=14)
        )
        self.url_entry.pack(side="left", padx=5)

        self.info_btn = customtkinter.CTkButton(
            url_frame,
            text="Get Info",
            command=self.fetch_video_info,
            width=120,
            height=40,
            font=customtkinter.CTkFont(size=14)
        )
        self.info_btn.pack(side="left", padx=5)

        # Video info frame (for thumbnail and details)
        self.info_display_frame = customtkinter.CTkFrame(self.app, width=880, height=200)
        self.info_display_frame.pack(pady=10)
        self.info_display_frame.pack_propagate(False)

        # Format selection frame (initially hidden)
        self.format_frame = customtkinter.CTkFrame(self.app, fg_color="transparent")

        self.format_label = customtkinter.CTkLabel(
            self.format_frame,
            text="Choose download format:",
            font=customtkinter.CTkFont(size=16)
        )
        self.format_label.grid(row=0, column=0, padx=20)

        self.audio_btn = customtkinter.CTkButton(
            self.format_frame,
            text="Audio (MP3)",
            command=self.show_audio_options,
            width=150,
            height=40,
            font=customtkinter.CTkFont(size=14)
        )
        self.audio_btn.grid(row=0, column=1, padx=10)

        self.video_btn = customtkinter.CTkButton(
            self.format_frame,
            text="Video (MP4)",
            command=self.show_video_options,
            width=150,
            height=40,
            font=customtkinter.CTkFont(size=14)
        )
        self.video_btn.grid(row=0, column=2, padx=10)

        # Options frame (for quality selection)
        self.options_frame = customtkinter.CTkFrame(self.app, width=880, height=80)
        self.options_frame.pack_propagate(False)

        # Status frame
        self.status_frame = customtkinter.CTkFrame(self.app, width=880, height=100)
        self.status_frame.pack(pady=10)
        self.status_frame.pack_propagate(False)


    def clear_dynamic_widgets(self):
        """Remove all dynamically created widgets."""
        for widget in self.dynamic_widgets:
            widget.destroy()
        self.dynamic_widgets.clear()

    def fetch_video_info(self):
        """Fetch video information and thumbnail in a separate thread."""
        # Validate URL
        is_valid, error_msg = self.validate_url(self.url_entry.get())
        if not is_valid:
            self.show_error(error_msg)
            return

        self.info_btn.configure(state="disabled")
        self.show_status("Fetching video information...")

        thread = threading.Thread(target=self._fetch_video_info_thread)
        thread.daemon = True
        thread.start()

    def _fetch_video_info_thread(self):
        """Thread function for fetching video info."""
        try:
            url = self.url_entry.get().strip()

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                self.video_info = info_dict

                # Download thumbnail
                thumbnail_url = info_dict.get('thumbnail')
                if thumbnail_url:
                    response = requests.get(thumbnail_url, timeout=10)
                    img = Image.open(BytesIO(response.content))

                    # Resize thumbnail to fit display
                    img.thumbnail((300, 200), Image.Resampling.LANCZOS)

                    # Save thumbnail temporarily
                    self.thumbnail_path = os.path.join(tempfile.gettempdir(), 'yt_thumb.jpg')
                    img.save(self.thumbnail_path)

                self.app.after(0, self.display_video_info)

        except Exception as e:
            error_msg = f"Failed to fetch video info: {str(e)}"
            self.app.after(0, self.show_error, error_msg)
            self.app.after(0, lambda: self.info_btn.configure(state="normal"))

    def display_video_info(self):
        """Display video information and thumbnail."""
        # Clear info frame
        for widget in self.info_display_frame.winfo_children():
            widget.destroy()

        # Clear status
        for widget in self.status_frame.winfo_children():
            widget.destroy()

        if not self.video_info:
            return

        # Create left frame for thumbnail
        left_frame = customtkinter.CTkFrame(self.info_display_frame, fg_color="transparent")
        left_frame.pack(side="left", padx=20, pady=10)

        # Display thumbnail
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            thumbnail_img = customtkinter.CTkImage(
                light_image=Image.open(self.thumbnail_path),
                dark_image=Image.open(self.thumbnail_path),
                size=(300, 200)
            )
            thumbnail_label = customtkinter.CTkLabel(left_frame, image=thumbnail_img, text="")
            thumbnail_label.image = thumbnail_img  # Keep reference
            thumbnail_label.pack()

        # Create right frame for info
        right_frame = customtkinter.CTkFrame(self.info_display_frame, fg_color="transparent")
        right_frame.pack(side="left", padx=20, pady=10, fill="both", expand=True)

        # Video details
        title = self.video_info.get('title', 'Unknown')
        uploader = self.video_info.get('uploader', 'Unknown')
        duration = self.video_info.get('duration', 0)
        view_count = self.video_info.get('view_count', 0)

        # Format duration
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02d}"

        # Format view count
        if view_count >= 1000000:
            views_str = f"{view_count / 1000000:.1f}M"
        elif view_count >= 1000:
            views_str = f"{view_count / 1000:.1f}K"
        else:
            views_str = str(view_count)

        info_texts = [
            ("Title:", title[:60] + "..." if len(title) > 60 else title),
            ("Channel:", uploader),
            ("Duration:", duration_str),
            ("Views:", views_str),
        ]

        for label_text, value_text in info_texts:
            row_frame = customtkinter.CTkFrame(right_frame, fg_color="transparent")
            row_frame.pack(anchor="w", pady=3)

            label = customtkinter.CTkLabel(
                row_frame,
                text=label_text,
                font=customtkinter.CTkFont(size=13, weight="bold"),
                width=80,
                anchor="w"
            )
            label.pack(side="left")

            value = customtkinter.CTkLabel(
                row_frame,
                text=value_text,
                font=customtkinter.CTkFont(size=13),
                anchor="w"
            )
            value.pack(side="left", padx=5)

        # Show format selection buttons
        self.format_frame.pack(pady=15)
        self.info_btn.configure(state="normal")

    def validate_url(self, url):
        """Validate YouTube URL format."""
        if not url or not url.strip():
            return False, "Please enter a URL"

        # Basic YouTube URL validation
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        if not re.match(youtube_regex, url):
            return False, "Please enter a valid YouTube URL"

        return True, ""

    def show_audio_options(self):
        """Display audio quality selection options."""
        self.clear_dynamic_widgets()
        self.options_frame.pack(pady=10)

        label = customtkinter.CTkLabel(
            self.options_frame,
            text="Select audio quality (kbps):",
            font=customtkinter.CTkFont(size=16)
        )
        label.pack(side="left", padx=20)
        self.dynamic_widgets.append(label)

        self.audio_quality_combo = customtkinter.CTkComboBox(
            self.options_frame,
            values=["128", "192", "256", "320"],
            width=200,
            height=35,
            font=customtkinter.CTkFont(size=14),
            state="readonly"
        )
        self.audio_quality_combo.set("192")  # Default value
        self.audio_quality_combo.pack(side="left", padx=10)
        self.dynamic_widgets.append(self.audio_quality_combo)

        download_btn = customtkinter.CTkButton(
            self.options_frame,
            text="Download",
            command=lambda: self.download_audio(self.audio_quality_combo.get()),
            width=150,
            height=35,
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        download_btn.pack(side="left", padx=10)
        self.dynamic_widgets.append(download_btn)

    def show_video_options(self):
        """Display video quality selection options."""
        self.clear_dynamic_widgets()
        self.options_frame.pack(pady=10)

        label = customtkinter.CTkLabel(
            self.options_frame,
            text="Select video quality (resolution):",
            font=customtkinter.CTkFont(size=16)
        )
        label.pack(side="left", padx=20)
        self.dynamic_widgets.append(label)

        self.video_quality_combo = customtkinter.CTkComboBox(
            self.options_frame,
            values=["360p", "480p", "720p", "1080p", "1440p", "2160p (4K)"],
            width=200,
            height=35,
            font=customtkinter.CTkFont(size=14),
            state="readonly"
        )
        self.video_quality_combo.set("720p")  # Default value
        self.video_quality_combo.pack(side="left", padx=10)
        self.dynamic_widgets.append(self.video_quality_combo)

        download_btn = customtkinter.CTkButton(
            self.options_frame,
            text="Download",
            command=lambda: self.download_video(self.video_quality_combo.get()),
            width=150,
            height=35,
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        download_btn.pack(side="left", padx=10)
        self.dynamic_widgets.append(download_btn)

    def show_status(self, message, is_error=False):
        """Display status message."""
        for widget in self.status_frame.winfo_children():
            widget.destroy()

        color = "#FF5555" if is_error else "#50C878"

        status_label = customtkinter.CTkLabel(
            self.status_frame,
            text=message,
            font=customtkinter.CTkFont(size=16),
            text_color=color
        )
        status_label.pack(expand=True)

    def show_error(self, message):
        """Display error message."""
        self.show_status(message, is_error=True)

    def download_audio(self, quality):
        """Download audio in a separate thread."""
        # Disable buttons during download
        self.audio_btn.configure(state="disabled")
        self.video_btn.configure(state="disabled")

        self.show_status(f"Downloading audio at {quality} kbps...")

        thread = threading.Thread(target=self._download_audio_thread, args=(quality,))
        thread.daemon = True
        thread.start()

    def _download_audio_thread(self, quality):
        """Thread function for audio download."""
        try:
            url = self.url_entry.get().strip()

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality,
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
                'restrictfilenames': True,
                'writethumbnail': True,
                'ignoreerrors': False,
                'quiet': True,
                'no_warnings': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get('title', 'Unknown')

                self.app.after(0, self.show_status, f"✓ Audio downloaded successfully!\nTitle: {title}\n\nReady for next download.")
                self.app.after(0, self.clear_dynamic_widgets)
                self.app.after(0, self.enable_buttons)

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.app.after(0, self.show_error, error_msg)
            self.app.after(0, self.enable_buttons)

    def download_video(self, quality_str):
        """Download video in a separate thread."""
        # Disable buttons during download
        self.audio_btn.configure(state="disabled")
        self.video_btn.configure(state="disabled")

        self.show_status(f"Downloading video at {quality_str}...")

        # Extract numeric quality
        quality = quality_str.split('p')[0].split('(')[0].strip()

        thread = threading.Thread(target=self._download_video_thread, args=(quality,))
        thread.daemon = True
        thread.start()

    def _download_video_thread(self, quality):
        """Thread function for video download."""
        try:
            url = self.url_entry.get().strip()

            ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegVideoConvertor',
                        'preferredformat': 'mp4',
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
                'restrictfilenames': True,
                'writethumbnail': True,
                'ignoreerrors': False,
                'quiet': True,
                'no_warnings': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get('title', 'Unknown')

                self.app.after(0, self.show_status, f"✓ Video downloaded successfully!\nTitle: {title}\n\nReady for next download.")
                self.app.after(0, self.clear_dynamic_widgets)
                self.app.after(0, self.enable_buttons)

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.app.after(0, self.show_error, error_msg)
            self.app.after(0, self.enable_buttons)

    def enable_buttons(self):
        """Re-enable download buttons."""
        self.audio_btn.configure(state="normal")
        self.video_btn.configure(state="normal")

    def reset_ui(self):
        """Reset the UI to initial state."""
        self.url_entry.delete(0, 'end')
        self.clear_dynamic_widgets()

        # Clear info display
        for widget in self.info_display_frame.winfo_children():
            widget.destroy()

        for widget in self.status_frame.winfo_children():
            widget.destroy()

        # Hide format frame and options frame
        self.format_frame.pack_forget()
        self.options_frame.pack_forget()

        self.enable_buttons()

        # Reset video info
        self.video_info = None
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            try:
                os.remove(self.thumbnail_path)
            except:
                pass
        self.thumbnail_path = None

    def run(self):
        """Start the application."""
        self.app.mainloop()


if __name__ == "__main__":
    downloader = YouTubeDownloader()
    downloader.run()