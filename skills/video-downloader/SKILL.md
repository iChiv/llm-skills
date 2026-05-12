---
name: video-downloader
description: Download videos from YouTube, Bilibili, Vimeo, and 1000+ other sites. Supports SponsorBlock skipping, chapter splitting, GIF/frame extraction, subtitles translation, batch downloads, auto-organize, archive dedup, and format inspection without downloading.
tool: yt-dlp
tool_args: --version
tool_upstream: yt-dlp/yt-dlp
---

# Video Downloader

Downloads videos from multiple platforms using **yt-dlp** (2026.03.17+) and **BBDown** for Bilibili. Includes post-processing: GIF extraction, frame capture, and video recoding via ffmpeg.

## Dependencies

| Tool | Required | Purpose |
|------|----------|---------|
| yt-dlp | Yes | Core download engine |
| ffmpeg | Yes | Post-processing (merge, GIF, frames, recode) |
| BBDown | Optional (Bilibili only) | Better Bilibili reliability |

## Quick Start

```python
import sys
sys.path.insert(0, 'C:/Users/happyelements/.claude/skills/video-downloader/scripts')
from video_downloader import download_video

# Basic download
download_video('https://www.youtube.com/watch?v=VIDEO_ID')

# Skip sponsor segments
download_video('https://www.youtube.com/watch?v=VIDEO_ID', no_sponsor=True)

# Split into chapters
download_video('https://www.youtube.com/watch?v=VIDEO_ID', split_chapters=True)

# Inspect without downloading
success, msg, extra = download_video('https://www.youtube.com/watch?v=VIDEO_ID', info_only=True)
print(extra['json'][0]['title'])

# GIF extraction (perfect for sports analysis)
download_video('https://www.youtube.com/watch?v=VIDEO_ID',
               extract_gif_enabled=True, gif_start=10, gif_duration=3,
               gif_fps=15, gif_width=640)

# Extract frames for frame-by-frame analysis
download_video('https://www.youtube.com/watch?v=VIDEO_ID',
               extract_frames_enabled=True, frame_interval=0.5)

# Batch download from a URL list
download_video('https://www.youtube.com/watch?v=PLAYLIST_ID',
               playlist=True, download_archive='archive.txt',
               organize=True, no_sponsor=True)
```

## All Parameters

### Download
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | required | Video or playlist URL |
| `output_dir` | str | Desktop | Where to save files |
| `quality` | str | `best` | `best`, `1080`, `720`, `480`, `worst` |
| `audio_only` | bool | False | Extract audio only |
| `format` | str | None | Preferred container: `mp4`, `webm`, `mkv` |
| `playlist` | bool | False | Download full playlist |
| `batch_file` | str | None | File with URLs (one per line) |
| `download_archive` | str | None | File to track downloaded IDs |

### Metadata & Quality of Life
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subtitles` | bool | False | Download + embed subtitles |
| `sub_translate` | str | None | Translate subs to language (e.g. `zh`, `en`) |
| `thumbnail` | bool | False | Embed thumbnail |
| `no_sponsor` | bool | False | Skip sponsor/self-promo/intro segments via SponsorBlock |
| `split_chapters` | bool | False | Split output into per-chapter files |
| `organize` | bool | False | Auto-sort into `platform/channel/` subdirectories |

### Inspection (no download)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `info_only` | bool | False | Return video metadata as JSON |
| `list_formats` | bool | False | List all available formats/qualities |

### Post-Processing
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `recode` | str | None | Re-encode: `mp4`, `mkv`, `webm` |
| `extract_gif_enabled` | bool | False | Generate GIF from downloaded video |
| `gif_start` | float | 0 | GIF start time (seconds) |
| `gif_duration` | float | 5 | GIF duration (seconds) |
| `gif_fps` | int | 10 | GIF frame rate |
| `gif_width` | int | 480 | GIF width in pixels |
| `extract_frames_enabled` | bool | False | Extract still frames at intervals |
| `frame_interval` | float | 1.0 | Time between frames (seconds) |

### Performance
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `concurrent_fragments` | int | None | Parallel download fragments |
| `cookies_from_browser` | str | None | Browser for auth: `chrome`, `firefox`, `edge` |
| `live_from_start` | bool | False | Download livestream from beginning |
| `rate_limit` | str | None | Speed cap: `1M`, `500K` |

## Platform Support

- **Bilibili** — auto-detected; uses BBDown for anti-scraping
- **YouTube** — shorts, playlists, livestreams, age-restricted
- **TikTok, Vimeo, Instagram, X/Twitter**, and 1000+ more via yt-dlp

## CLI Usage

```bash
python video_downloader.py <URL> [options]

# Download with sponsor skipping
python video_downloader.py "https://youtube.com/watch?v=..." --no-sponsor

# Split chapters
python video_downloader.py "https://youtube.com/watch?v=..." --split-chapters

# Inspect metadata
python video_downloader.py "https://youtube.com/watch?v=..." --info

# Batch + organize + archive
python video_downloader.py "https://youtube.com/playlist?list=..." \
    --playlist --organize --download-archive archive.txt --no-sponsor

# GIF from downloaded video
python video_downloader.py "https://youtube.com/watch?v=..." \
    --extract-gif --gif-start 30 --gif-duration 5 --gif-fps 15 --gif-width 640

# Extract frames
python video_downloader.py "https://youtube.com/watch?v=..." \
    --extract-frames --frame-interval 0.5

# Translate subtitles to Chinese
python video_downloader.py "https://youtube.com/watch?v=..." \
    --sub-translate zh --subtitles
```

## Error Handling

Handles: invalid URLs, network issues, missing dependencies, age-restricted content, geo-blocking, Bilibili anti-scraping. Errors include clear messages and suggestions.
