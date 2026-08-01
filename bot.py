ydl_opts = {
    'format': 'best[ext=mp4]/best',
    'outtmpl': filename,
    'quiet': True,
    'noplaylist': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],  # ជៀសវាង web client ដែលត្រូវការ n-challenge
        }
    },
}
