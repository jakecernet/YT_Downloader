import os
from turtle import title
from yt_dlp import YoutubeDL
title = "YouTube Downloader"

def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ignoreerrors': True,
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
            'quiet': True,
            'ignoreerrors': True,
        }

        ydl = YoutubeDL(ydl_opts)

        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', None)

        print("Video downloaded as MP3 successfully!")

    except Exception as e:
        print("An error occurred:", str(e))


if __name__ == "__main__":
    video_url = input("\nEnter the YouTube video URL: ")
    print("\nDownloading...\n")
    download_video(video_url)
    print("---------------------------------")
    print("Thank you for using the YouTube Downloader!") 