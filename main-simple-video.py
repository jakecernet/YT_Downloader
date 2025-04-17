from yt_dlp import YoutubeDL
title = "YouTube Downloader"

def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
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

        print("Video downloaded as MP4 successfully!")
        print("Video Title:", video_title)

    except Exception as e:
        print("An error occurred:", str(e))


if __name__ == "__main__":
    video_url = input("\nEnter the YouTube video URL: ")
    print("\nDownloading...\n")
    download_video(video_url)
    print("---------------------------------")
    print("Thank you for using the YouTube Downloader!") 