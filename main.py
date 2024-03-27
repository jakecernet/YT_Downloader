import os
from turtle import title
from yt_dlp import YoutubeDL
title = "YouTube Downloader"

def download(url):
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

main()