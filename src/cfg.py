ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

base_url = "https://www.youtube.com"
max_minutes = 19
download_dir = "downloads"

attempts = 5
wait_time = [5, 5, 10, 15, 60]
