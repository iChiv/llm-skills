---
name: video-downloader
description: Download videos from YouTube, Bilibili, Vimeo, and 1000+ other websites. Use this skill when users ask to: (1) Download videos from URLs, (2) Save YouTube videos, (3) Download Bilibili videos, (4) Extract audio from videos, (5) Download video playlists. Automatically detects Bilibili URLs and uses BBDown for reliable downloads. Automatically saves to user's Desktop. Supports quality selection, format conversion, and batch downloads.
---

# Video Downloader

This skill downloads videos from multiple platforms using specialized downloaders:
- **yt-dlp** (2026.03.17+) for YouTube, Vimeo, and 1000+ other sites
- **BBDown** for Bilibili (automatically detected for better reliability)
- **ffmpeg** is required by yt-dlp for video post-processing (merging, format conversion)

## Dependencies

The skill requires these tools to be available in PATH:

| Tool | Required | Purpose | Download |
|------|----------|---------|----------|
| yt-dlp | Yes | Core download engine | `pip install yt-dlp` or [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/releases) |
| ffmpeg | Yes | Post-processing (merge video+audio, format conversion) | [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (Windows) or [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) |
| BBDown | Optional | Bilibili downloads | [BBDown](https://github.com/nilaoda/BBDown) |

### ffmpeg Installation (Windows)
1. Download `ffmpeg-release-essentials.zip` from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to system PATH

## Quick Start

To download a video, simply provide the URL. The script automatically:
- Detects Bilibili URLs and uses BBDown
- Uses yt-dlp for all other sites
- Saves to the user's Desktop
- Warns if ffmpeg is not found in PATH

Example usage:
```python
import sys
sys.path.insert(0, 'C:/Users/happyelements/.claude/skills/video-downloader/scripts')
from video_downloader import download_video

# Basic download (best quality)
download_video('https://www.youtube.com/watch?v=VIDEO_ID')

# Download Bilibili video (auto-detects and uses BBDown)
download_video('https://www.bilibili.com/video/BV1xx411c7mD')

# Download specific quality
download_video('https://www.youtube.com/watch?v=VIDEO_ID', quality='720')

# Download audio only
download_video('https://www.youtube.com/watch?v=VIDEO_ID', audio_only=True)

# Faster download with concurrent fragments
download_video('https://www.youtube.com/watch?v=VIDEO_ID', concurrent_fragments=4)

# Use browser cookies for age-restricted content
download_video('https://www.youtube.com/watch?v=VIDEO_ID', cookies_from_browser='chrome')

# Download livestream from the beginning
download_video('https://www.youtube.com/watch?v=VIDEO_ID', live_from_start=True)

# Limit download speed
download_video('https://www.youtube.com/watch?v=VIDEO_ID', rate_limit='1M')
```

## Common Options

The `download_video()` function supports these parameters:

- **url** (required): Video URL
- **output_dir** (optional): Output directory (defaults to Desktop)
- **quality** (optional): Video quality ('best', '1080', '720', '480', 'worst')
- **audio_only** (optional): Download audio only (default: False)
- **format** (optional): Preferred format ('mp4', 'webm', 'mkv', etc.)
- **playlist** (optional): Download entire playlist (default: False)
- **subtitles** (optional): Download subtitles (default: False)
- **thumbnail** (optional): Embed thumbnail (default: False)
- **use_bbdown** (optional): Force use BBDown (default: auto-detect)
- **concurrent_fragments** (optional): Number of concurrent fragments for faster downloads (e.g. 4)
- **cookies_from_browser** (optional): Browser to extract cookies from ('chrome', 'firefox', 'edge', etc.)
- **live_from_start** (optional): Download livestream from the beginning (default: False)
- **rate_limit** (optional): Download speed limit (e.g. '1M', '500K')

## Platform Support

### Bilibili (BBDown)
Automatically detected for URLs containing:
- `bilibili.com/video`
- `b23.tv`
- `bilibili.com/bangumi`

BBDown is used for Bilibili because it handles:
- Bilibili's anti-scraping mechanisms
- DASH format streams
- Geo-restrictions
- Login requirements (when needed)

### TikTok
Recent yt-dlp versions include improved TikTok challenge solving. For TikTok downloads, no special configuration needed.

### Other Platforms (yt-dlp)
Supports 1000+ sites including:
- YouTube (all formats, Shorts, playlists, livestreams)
- Vimeo
- Twitter/X
- Instagram
- TikTok
- Patreon
- SoundCloud
- And many more

## Quality Selection

- `quality='best'` - Best available quality (default)
- `quality='1080'` - 1080p or best available
- `quality='720'` - 720p or best available
- `quality='480'` - 480p or best available
- `quality='worst'` - Worst quality (smallest file)

## Advanced Features

### Browser Cookies

For sites requiring login or age verification, use browser cookies:

```python
download_video(url, cookies_from_browser='chrome')
download_video(url, cookies_from_browser='firefox')
download_video(url, cookies_from_browser='edge')
```

### Concurrent Downloads

Speed up downloads by using concurrent fragments:

```python
download_video(url, concurrent_fragments=4)  # Use 4 concurrent connections
```

### Livestream Downloads

Download a live stream from the beginning:

```python
download_video(livestream_url, live_from_start=True)
```

### Rate Limiting

Throttle download speed:

```python
download_video(url, rate_limit='500K')   # 500 KB/s
download_video(url, rate_limit='1M')     # 1 MB/s
```

### Advanced yt-dlp Options

For advanced yt-dlp options not covered by the wrapper, directly execute yt-dlp commands using the Bash tool.

See [references/yt-dlp-options.md](references/yt-dlp-options.md) for comprehensive option reference.

## Error Handling

The script handles common errors:
- Invalid or unavailable URLs
- Network issues
- File system errors
- Age-restricted or geo-blocked content
- Bilibili anti-scraping (using BBDown)
- Missing dependencies (yt-dlp, ffmpeg)

Errors are reported with clear messages to help users understand what went wrong.

## Updating

To update the underlying tools:
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Check current versions
yt-dlp --version
ffmpeg -version
```
