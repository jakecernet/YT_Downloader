from yt_dlp import YoutubeDL

def download_audio(url):
    """Download YouTube video and convert to MP3 audio."""
    if not url or not url.strip():
        print("Error: URL cannot be empty!")
        return False

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
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
            'quiet': True,
            'ignoreerrors': False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Unknown')
            print(f"'{video_title}' downloaded as MP3 successfully!")
            return True

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    print("=== YouTube Audio Downloader ===")
    video_url = input("\nEnter the YouTube video URL: ")
    print("\nDownloading...\n")

    if download_audio(video_url):
        print("---------------------------------")
        print("Thank you for using the YouTube Downloader!")
    else:
        print("---------------------------------")
        print("Download failed. Please try again.") 