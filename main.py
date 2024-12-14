import customtkinter
from yt_dlp import YoutubeDL

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

app = customtkinter.CTk()
app.geometry("800x200")

def audio_download():
    quality = customtkinter.CTkLabel(app, text="What quality do you want to convert the audio to?")
    quality.place(relx=0.28, rely=0.5, anchor=customtkinter.CENTER)

    combobox = customtkinter.CTkComboBox(app, values=["128", "192", "256", "320"], command=downloadAudio)
    combobox.place(relx=0.8, rely=0.5, anchor=customtkinter.CENTER)    

def video_download():
    quality = customtkinter.CTkLabel(app, text="What quality do you want to convert the video to?")
    quality.place(relx=0.28, rely=0.5, anchor=customtkinter.CENTER)

    combobox = customtkinter.CTkComboBox(app, values=["144", "240", "360", "480", "720", "1080", "1440", "2160"], command=downloadVideo)
    combobox.place(relx=0.8, rely=0.5, anchor=customtkinter.CENTER)

def downloadAudio(choice):
    wait = customtkinter.CTkLabel(app, text="Downloading at " + choice + " kbps")
    wait.place(relx=0.5, rely=0.7, anchor=customtkinter.CENTER)

    ydl_opts = {
        'format': 'bestaudio/best', 
        'postprocessors': [{ 
            'key': 'FFmpegExtractAudio', 
            'preferredcodec': 'mp3', 
            'preferredquality': choice, 
            }],
        'outtmpl': '%(title)s.%(ext)s', 
        'restrictfilenames': True, 
        'ignoreerrors': True,
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydtl:
        ydtl.download([url.get()])

    done = customtkinter.CTkLabel(app, text="Audio Downloaded")
    done.place(relx=0.5, rely=0.9, anchor="center")

def downloadVideo(choice):
    ydl_opts = {
        'outtmpl': '/%(title)s.%(ext)s',
        'format': 'bestvideo[height<={}]'.format(choice) + '+bestaudio/best',
        'postprocessors': [{ 
            'key': 'FFmpegVideoConvertor', 
            'preferedformat': 'mp4', 
            }],
        'outtmpl': '%(title)s.%(ext)s', 
        'restrictfilenames': True, 
        'ignoreerrors': True,
        'quiet': True,
        'writesubtitles': True,
        'allsubtitles': True,
        'subtitlesformat': 'srt',
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url.get()])

    done = customtkinter.CTkLabel(app, text="Video Downloaded")
    done.place(relx=0.5, rely=0.9, anchor=customtkinter.CENTER)

url = customtkinter.CTkEntry(app, placeholder_text="Enter the URL of the video you want to download", width=650)
url.place(relx=0.5, rely=0.1, anchor=customtkinter.CENTER)

format = customtkinter.CTkLabel(app, text="Do you want to download audio or video?")
format.place(relx=0.25, rely=0.3, anchor=customtkinter.CENTER)

audio = customtkinter.CTkButton(master=app, text="Audio", command=audio_download)
audio.place(relx=0.6, rely=0.3, anchor=customtkinter.CENTER)

video = customtkinter.CTkButton(master=app, text="Video", command=video_download)
video.place(relx=0.8, rely=0.3, anchor=customtkinter.CENTER)

app.mainloop()