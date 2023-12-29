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
                'preferredquality': quality,
            }],
            'ignoreerrors': True,  # Add this option to ignore errors and continue downloading
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
    print("---------------------------------------------------------------------------------")
    print("|                                                                               |")
    print("|                        Welcome to the YouTube Downloader!                     |")
    print("|                                                                               |")
    print("---------------------------------------------------------------------------------")
    print("")
    quality = input("Enter the bitrate of the audio you want to download (128, 192, 256, 320): ")
    print("")
    video_url = input("Enter the YouTube video URL: ")
    print("")
    print("---------------------------------------------------------------------------------")
    print("|                                                                               |")
    print("|                          Downloading your video...                            |")
    print("|                                                                               |")
    print("---------------------------------------------------------------------------------")
    print("")
    download_video(video_url)
    print("")
    print("---------------------------------------------------------------------------------")
    print("|                                                                               |")
    print("|                       Thank you for using this program!                       |")
    print("|                                                                               |")
    print("---------------------------------------------------------------------------------")
    print("")
    input("Press enter to exit...")