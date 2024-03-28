import os
import customtkinter
from turtle import title
from yt_dlp import YoutubeDL
title = "YouTube Downloader"

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

app = customtkinter.CTk()
app.geometry("800x540")

def audio_download():
    quality = customtkinter.CTkLabel(app, text="What quality do you want to convert the audio to?")
    quality.place(relx=0.5, rely=0.6, anchor=customtkinter.CENTER)

    btn_128 = customtkinter.CTkButton(master=app, text="128 kbps", command=audio128)
    btn_128.place(relx=0.2, rely=0.7, anchor=customtkinter.CENTER)

    btn_192 = customtkinter.CTkButton(master=app, text="192 kbps", command=audio192)
    btn_192.place(relx=0.4, rely=0.7, anchor=customtkinter.CENTER)

    btn_256 = customtkinter.CTkButton(master=app, text="256 kbps", command=audio256)
    btn_256.place(relx=0.6, rely=0.7, anchor=customtkinter.CENTER)

    btn_320 = customtkinter.CTkButton(master=app, text="320 kbps", command=audio320)
    btn_320.place(relx=0.8, rely=0.7, anchor=customtkinter.CENTER)

def video_download():
    quality = customtkinter.CTkLabel(app, text="What quality do you want to convert the video to? (144, 240, 360, 480, 720, 1080, 1440, 2160)")
    quality.place(relx=0.5, rely=0.6, anchor=customtkinter.CENTER)

    btn_144 = customtkinter.CTkButton(master=app, text="144", command=video144)
    btn_144.place(relx=0.2, rely=0.7, anchor=customtkinter.CENTER)

    btn_240 = customtkinter.CTkButton(master=app, text="240", command=video240)
    btn_240.place(relx=0.3, rely=0.7, anchor=customtkinter.CENTER)

    btn_360 = customtkinter.CTkButton(master=app, text="360", command=video360)
    btn_360.place(relx=0.4, rely=0.7, anchor=customtkinter.CENTER)

    btn_480 = customtkinter.CTkButton(master=app, text="480", command=video480)
    btn_480.place(relx=0.5, rely=0.7, anchor=customtkinter.CENTER)

    btn_720 = customtkinter.CTkButton(master=app, text="720", command=video720)
    btn_720.place(relx=0.6, rely=0.7, anchor=customtkinter.CENTER)

    btn_1080 = customtkinter.CTkButton(master=app, text="1080", command=video1080)  
    btn_1080.place(relx=0.7, rely=0.7, anchor=customtkinter.CENTER)

    btn_1440 = customtkinter.CTkButton(master=app, text="1440", command=video1440)
    btn_1440.place(relx=0.8, rely=0.7, anchor=customtkinter.CENTER)

    btn_2160 = customtkinter.CTkButton(master=app, text="2160", command=video2160)
    btn_2160.place(relx=0.9, rely=0.7, anchor=customtkinter.CENTER)

def audio128():
    audioDownloader(128)

def audio192():
    audioDownloader(192)

def audio256():
    audioDownloader(256)

def audio320():
    audioDownloader(320)

def audioDownloader(quality):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url.get()])
   
    done = customtkinter.CTkLabel(app, text="Audio downloaded successfully")
    done.place(relx=0.5, rely=0.9, anchor=customtkinter.CENTER)

def video144():
    videoDownloader(144)

def video240():
    videoDownloader(240)

def video360():
    videoDownloader(360)

def video480():
    videoDownloader(480)

def video720():
    videoDownloader(720)

def video1080():
    videoDownloader(1080)

def video1440():
    videoDownloader(1440)

def video2160():
    videoDownloader(2160)

def videoDownloader(videoQuality):
    ydl_opts = {
        'format': 'bestvideo[height<={}]'.format(videoQuality) + '+bestaudio/best',
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url.get()])
    
    done = customtkinter.CTkLabel(app, text="Video downloaded successfully")
    done.place(relx=0.5, rely=0.9, anchor=customtkinter.CENTER)

# Main functions
url = customtkinter.CTkEntry(app, placeholder_text="Enter the URL of the video you want to download", width=650)
url.place(relx=0.5, rely=0.3, anchor=customtkinter.CENTER)

format = customtkinter.CTkLabel(app, text="Do you want to download audio or video?")
format.place(relx=0.5, rely=0.4, anchor=customtkinter.CENTER)

audio = customtkinter.CTkButton(master=app, text="Audio", command=audio_download)
audio.place(relx=0.3, rely=0.5, anchor=customtkinter.CENTER)

video = customtkinter.CTkButton(master=app, text="Video", command=video_download)
video.place(relx=0.7, rely=0.5, anchor=customtkinter.CENTER)

app.mainloop()

""" def download(url):
    format = input("Do you want to download audio or video? (Audio - 1, Video - 2) ")
    
    if format == "1":
        convert = input("Do you want to convert the audio MP3? (Y, N) ")
        quality = input("What quality do you want to convert the audio to? (128, 192, 256, 320) ")

        if convert == "Y":
            keep = input("Do you want to keep the original audio file? (Y, N) ")
            if keep == "Y":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality,
                    }],
                    'keepvideo': True,
                }
            else:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality,
                    }],
                    'keepvideo': False,
                }
        else:
            ydl_opts = {
                'format': 'bestaudio/best',
                'preferredquality': quality,
            }

    elif format == "2":
        convert = input("Do you want to convert the video to MP4? (Y, N) ")
        quality = input("What quality do you want to convert the video to? (144, 240, 360, 480, 720, 1080, 1440, 2160) ")

        if convert == "Y":
            ydl_opts = {
                'format': 'bestvideo[height<={}]'.format(quality) + '+bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }
        else:
            ydl_opts = {
                'format': 'bestvideo[height<={}]'.format(quality) + '+bestaudio/best',
            }
        
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
def main():
    url = input("Enter the URL of the video you want to download: ")
    download(url)

main() """