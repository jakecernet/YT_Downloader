import os
from turtle import title
from yt_dlp import YoutubeDL
title = "YouTube Downloader"


def download_video(url):
    try:
        # Set options for yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '256',
            }],
        }

        # Create a YoutubeDL object
        ydl = YoutubeDL(ydl_opts)

        # Download the video and extract audio as MP3
        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', None)

        # Move the downloaded MP3 file to the "Downloads" folder
        output_folder = os.path.expanduser("~")
        output_path = os.path.join(output_folder, video_title + ".mp3")

        print("Video downloaded as MP3 successfully!")

    except Exception as e:
        print("An error occurred:", str(e))


if __name__ == "__main__":
    print("---------------------------------")
    print("Welcome to the YouTube Downloader!")
    print("---------------------------------")
    print("")
    print("---------------------------------")
    video_url = input("Enter the YouTube video URL: ")
    print("---------------------------------")
    print("Downloading...")
    download_video(video_url)
    print("---------------------------------")
    print("Thank you for using the YouTube Downloader!")
