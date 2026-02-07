from yt_dlp import YoutubeDL
title = "YouTube Downloader"

def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'socket_timeout': 30,
            'ignoreerrors': False,
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
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
        ydl = YoutubeDL(ydl_opts)

        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', None)

        print("\nVideo downloaded as MP4 successfully!")
        print("Video Title:", video_title)

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your internet connection is stable")
        print("2. Try updating yt-dlp: pip install --upgrade yt-dlp")
        print("3. Try a different video or check if the URL is correct")
        print("4. YouTube may be blocking requests - try again in a few moments")


if __name__ == "__main__":
    video_url = input("\nEnter the YouTube video URL: ")
    print("\nDownloading...\n")
    download_video(video_url)
    print("---------------------------------")
    print("Thank you for using the YouTube Downloader!") 