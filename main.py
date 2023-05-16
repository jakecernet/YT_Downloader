import os
import tkinter as tk
from tkinter import filedialog
from yt_dlp import YoutubeDL

def download_video():
    video_url = url_entry.get()

    try:
        # Set options for yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # Create a YoutubeDL object
        ydl = YoutubeDL(ydl_opts)

        # Download the video and extract audio as MP3
        info_dict = ydl.extract_info(video_url, download=True)
        video_title = info_dict.get('title', None)

        # Move the downloaded MP3 file to the chosen folder
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if output_folder:
            output_path = os.path.join(output_folder, video_title + ".mp3")
            os.rename(info_dict['filepath'], output_path)
            result_label.config(text="Video downloaded as MP3 successfully!", fg="green")
        else:
            result_label.config(text="Download cancelled.", fg="red")

    except Exception as e:
        result_label.config(text="An error occurred: " + str(e), fg="red")

# Create the main window
window = tk.Tk()
window.title("YT_Downloader")

# Create URL input label and entry
url_label = tk.Label(window, text="YouTube Video URL:")
url_label.pack()
url_entry = tk.Entry(window, width=50)
url_entry.pack()

# Create download button
download_button = tk.Button(window, text="Download", command=download_video)
download_button.pack(pady=10)

# Create result label
result_label = tk.Label(window, text="")
result_label.pack()

# Configure window padding and center it on the screen
window.configure(padx=20, pady=20)
window.update_idletasks()
window_width = window.winfo_width()
window_height = window.winfo_height()
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Run the main window loop
window.mainloop()
