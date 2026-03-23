from yt_dlp import YoutubeDL

def download_video(url):
    """Download YouTube video in MP4 format (up to 720p)."""
    if not url or not url.strip():
        print("Error: URL cannot be empty!")
        return False

    try:
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'postprocessors': [
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
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
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'socket_timeout': 30,
            'ignoreerrors': False,
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
            'writethumbnail': True,
            'quiet': False,
            'no_warnings': False,
            'extractor_args': {
                'youtube': {
                    # Use android client to bypass SABR streaming and bot detection
                    # Note: Without PO token, may be limited to lower quality formats (360p-720p)
                    'player_client': ['android'],
                }
            },
        }

        print("Attempting to download video...")
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Unknown')

            print(f"\n'{video_title}' downloaded as MP4 successfully!")
            return True

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your internet connection is stable")
        print("2. Try updating yt-dlp: pip install --upgrade yt-dlp")
        print("3. Try a different video or check if the URL is correct")
        print("4. YouTube may be blocking requests - try again in a few moments")
        return False


if __name__ == "__main__":
    print("=== YouTube Video Downloader ===")
    video_url = input("\nEnter the YouTube video URL: ")
    print("\nDownloading...\n")

    if download_video(video_url):
        print("---------------------------------")
        print("Thank you for using the YouTube Downloader!")
    else:
        print("---------------------------------")
        print("Download failed. Please try again.") 