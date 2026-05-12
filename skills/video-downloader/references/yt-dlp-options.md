# yt-dlp Options Reference

Comprehensive reference for advanced yt-dlp options not covered by the video_downloader.py wrapper.

## Format Selection

### Basic Format Selection
```
-f best              # Best quality
-f worst             # Worst quality
-f bestvideo+bestaudio  # Best video and audio separately
```

### Specific Quality
```
-f 'bestvideo[height<=1080]+bestaudio'  # Max 1080p
-f 'bestvideo[height<=720]+bestaudio'   # Max 720p
-f 'bestvideo[height<=480]+bestaudio'   # Max 480p
```

### Format Preference
```
-f 'mp4'             # MP4 only
-f 'webm'            # WebM only
-f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]'  # MP4 video + M4A audio
```

### Audio Quality
```
-f 'bestaudio'       # Best audio quality
-f 'bestaudio[abr<=128]'  # Max 128kbps bitrate
-x --audio-format mp3     # Extract to MP3
-x --audio-format m4a     # Extract to M4A
```

## Output Options

### Filename Template
```
-o '%(title)s.%(ext)s'           # Title only
-o '%(title)s-%(id)s.%(ext)s'    # Title + ID
-o '%(uploader)s/%(title)s.%(ext)s'  # Subfolder by uploader
-o '%(playlist_index)s-%(title)s.%(ext)s'  # Playlist index
```

### Available Fields
- `%(title)s` - Video title
- `%(id)s` - Video ID
- `%(uploader)s` - Uploader name
- `%(upload_date)s` - Upload date (YYYYMMDD)
- `%(duration)s` - Duration in seconds
- `%(view_count)s` - View count
- `%(like_count)s` - Like count
- `%(playlist_index)s` - Position in playlist
- `%(ext)s` - File extension

## Download Options

### Playlist Handling
```
--yes-playlist        # Download entire playlist
--no-playlist         # Download single video only
--playlist-start 5    # Start from video #5
--playlist-end 10     # End at video #10
--playlist-items 1,3,5  # Download specific videos
```

### Subtitles
```
--sub-langs all,en    # Download all or specific languages
--write-subs          # Write subtitles
--write-auto-subs     # Write auto-generated subtitles
--embed-subs          # Embed subtitles in video
--sub-format srt      # Subtitle format (srt/ass/vtt)
```

### Metadata
```
--embed-thumbnail     # Embed thumbnail as cover art
--embed-metadata      # Embed metadata
--add-metadata        # Add metadata to file
--write-info-json     # Write video info as JSON
--write-description   # Write description to file
```

### Quality Control
```
--format-sort quality # Prefer quality over everything
--format-sort '+res'  # Prefer higher resolution
--format-sort '+size' # Prefer smaller file size
```

## Performance Options

### Download Speed
```
--concurrent-fragments 4  # Download fragments concurrently
--limit-rate 1M           # Limit download rate to 1MB/s
--buffer-size 16K         # Buffer size
```

### Retry Handling
```
--retries 10          # Number of retries
--fragment-retries 10  # Retries per fragment
--skip-unavailable-fragments  # Skip unavailable fragments
```

## Authentication

### YouTube
```
--username <email>    # YouTube email
--password <password> # YouTube password
--cookies cookies.txt # Use cookies file
```

### General
```
--username <user>
--password <pass>
--video-password <pass>  # For password-protected videos
```

## Post-Processing

### Conversion
```
--convert-format mp4  # Convert to MP4 after download
--convert-format mp3  # Convert to MP3 after download
--audio-quality 0     # Best audio quality (0-9, 0=best)
```

### Embedding
```
--embed-thumbnail     # Embed thumbnail
--embed-subs          # Embed subtitles
--embed-metadata      # Embed metadata
```

### Splitting
```
--split-chapters      # Split video into chapters
--split-time 00:05:00 # Split every 5 minutes
```

## Advanced Options

### Proxy
```
--proxy http://127.0.0.1:8080
```

### User Agent
```
--user-agent "Mozilla/5.0..."
```

### Referer
```
--referer "https://www.youtube.com"
```

### Cookies
```
--cookies cookies.txt
--cookies-from-browser chrome  # Use Chrome cookies
--cookies-from-browser firefox # Use Firefox cookies
```

## Info Extraction

### List Formats
```
--list-formats        # List all available formats
-F                    # Short form
```

### Get Info Only
```
--skip-download       # Don't download, just get info
--dump-json           # Dump info as JSON
--flat-playlist       # Don't download, just list playlist
```

## Examples

### Download specific quality with subtitles
```
yt-dlp -f 'bestvideo[height<=1080]+bestaudio' --sub-langs en --write-subs --embed-subs [URL]
```

### Download playlist, starting from video 5
```
yt-dlp --playlist-start 5 [URL]
```

### Download audio as MP3
```
yt-dlp -x --audio-format mp3 --audio-quality 0 [URL]
```

### Download with metadata and thumbnail
```
yt-dlp --embed-metadata --embed-thumbnail --add-metadata [URL]
```

### Download to specific folder with custom name
```
yt-dlp -o "C:/Videos/%(title)s.%(ext)s" [URL]
```

### Download with rate limiting
```
yt-dlp --limit-rate 500K [URL]
```
