# YT Downloader

Simple YouTube downloading script that allows you to download YouTube videos and extract their audio in MP3 and MP4 format. It utilizes the `yt_dlp` library to handle the download and FFmpeg to convert the downloaded video to MP3/MP4.

There are two versions of the script: Main and Main-simple. The Main version is the full version with more features, like downloading videos at custom quality and in MP4 format. The Main-simple version is a simplified version of the script that only allows you to download videos at 192kbps.

The script is cross-platform and can be run on Windows, Linux, and macOS. If you're on Windows, you can also run the executable file.

## Features

-   Download YouTube videos and playlists as MP3 and MP4 files
-   Download YouTube Music playlists as MP3 and MP4 files

## Requirements

-   Python 3.6 or higher if you're running the script from source
-   Windows 7 or higher if you're running the executable
-   FFmpeg must be installed and added to PATH (for converting videos to MP3/MP4, otherwise the script will download the video in WEBM format)
    <br>
    <br>

# Usage (Main)

### Windows:

-   Run the executable file
-   Select the preferred audio quality and format
-   Enter the URL of the YouTube video you want to download
-   The script will download the video and save it as an MP3 file in the folder where the executable is located

### Linux/macOS:

-   Run the command: `pip install -r requirements.txt` to install the libraries
-   Run the command: `python main.py`
-   Do the same steps as in the Windows version

<br>
<br>

# Usage (Main-simple)

### Windows:

-   Run the executable file
-   Paste the URL of the YouTube video you want to download
-   The script will download the video and save it as an MP3 file in the folder where the executable is located at 192kbps

### Linux/macOS:

-   Run the command: `pip install -r requirements.txt` to install the libraries
-   Run the command: `python main-simple.py`
-   Do the same steps as in the Windows version
