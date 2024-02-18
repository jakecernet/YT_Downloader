# YT Downloader
YT Downloader is a Python script that allows you to download YouTube videos and extract their audio in MP3 format. It utilizes the `yt_dlp` library to handle the download and FFmpeg to convert the downloaded video to MP3. The script is cross-platform and can be run on Windows, Linux, and macOS. It can be run from source or as an executable file.

## Features
 - Download YouTube videos and playlists as MP3 files
 - Download YouTube Music playlists as MP3 files

## Requirements
- Python 3.6 or higher if you're running the script from source
- Windows 7 or higher if you're running the executable
- FFmpeg must be installed and added to PATH (for converting videos to MP3, otherwise the script will download the video in WEBM format)

# Usage
### Windows:
 - Run the executable file
 - Select the preferred audio quality and format
 - Enter the URL of the YouTube video you want to download
 - The script will download the video and save it as an MP3 file in the folder where the executable is located

### Linux/macOS:
- Run the command: `pip install -r requirements.txt` to install the libraries
- Run the command: `python main.py`
- Do the same steps as in the Windows version

## Disclaimer
Please note that downloading YouTube videos may infringe on the platform's terms of service and may be subject to legal restrictions. Ensure that you have the necessary rights or permissions to download and use the content before proceeding. The script is provided for educational purposes only, and the responsibility for its usage lies with the user.

## Acknowledgments
YT_Downloader is built using the yt_dlp library, which is a community-driven fork of youtube-dl. Special thanks to the developers and contributors of yt_dlp for providing a powerful tool for downloading YouTube content.
