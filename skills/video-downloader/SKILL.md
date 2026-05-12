---
name: video-downloader
description: Download videos from YouTube, Bilibili, Vimeo, and 1000+ other sites. Supports SponsorBlock skipping, chapter splitting, GIF/frame extraction, subtitles translation, batch downloads, auto-organize, archive dedup, and format inspection without downloading.
tool: yt-dlp
tool_args: --version
tool_upstream: yt-dlp/yt-dlp
---

# Video Downloader

Downloads from multiple platforms using **yt-dlp** and **BBDown** for Bilibili. Post-processing: GIF, frames, recode via ffmpeg.

## Dependencies

| Tool | Required | Purpose |
|------|----------|---------|
| yt-dlp | Yes | Core download engine |
| ffmpeg | Yes | Post-processing |
| BBDown | Optional | Better Bilibili reliability |

## Quick Start

```python
import sys
sys.path.insert(0, 'C:/Users/happyelements/.claude/skills/video-downloader/scripts')
from video_downloader import download_video

download_video('https://www.youtube.com/watch?v=VIDEO_ID')
download_video('https://www.youtube.com/watch?v=VIDEO_ID', no_sponsor=True)
download_video('https://www.youtube.com/watch?v=VIDEO_ID', split_chapters=True)
ok, msg, extra = download_video('https://www.youtube.com/watch?v=VIDEO_ID', info_only=True)
download_video(url, extract_gif_enabled=True, gif_start=10, gif_duration=3, gif_fps=15, gif_width=640)
```

## All Parameters (see function signature for full list)

Key parameters: `url`, `output_dir`, `quality`, `audio_only`, `format`, `playlist`, `subtitles`, `sub_translate`, `thumbnail`, `no_sponsor`, `split_chapters`, `organize`, `info_only`, `list_formats`, `recode`, `extract_gif_enabled` (+ gif params), `extract_frames_enabled` (+ `frame_interval`), `cookies_from_browser`, `concurrent_fragments`, `live_from_start`, `rate_limit`, `download_archive`, `batch_file`.

## Member-Only & Paid Content

Downloading videos behind a login wall (Bilibili paid courses, YouTube member-only, age-restricted) is supported via browser cookies. **No extra tools needed.**

```python
download_video('https://www.bilibili.com/video/BV...', cookies_from_browser='chrome')
```

```bash
python video_downloader.py "https://www.bilibili.com/video/BV..." --cookies-from-browser chrome
```

Log in to the site in your browser first; yt-dlp reads the active session automatically.

Alternatively, export a portable `cookies.txt` with [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) and use: `yt-dlp --cookies cookies.txt <URL>`.

### Troubleshooting browser cookies

If `cookies_from_browser` fails:

| Problem | Likely cause | Fix |
|---------|-------------|------|
| Permission / locked DB error | Chrome is running (write lock) | **Close Chrome completely**, retry |
| Decryption error | New Chrome encryption (130+) | `pip install --upgrade yt-dlp` |
| Cookies read but no access | Wrong Chrome profile | Try `cookies_from_browser='chrome:Profile 1'` |
| All of the above fail | OS-level decryption issue | Fall back to `cookies.txt` export (always works) |

Try alternate browsers/profiles: `edge`, `brave`, `chrome:Default`, `chrome:Profile 1`.

Keep yt-dlp updated: `pip install --upgrade yt-dlp`. Version should be >= 2025.03.

## Platform Support

- **Bilibili** — auto-detected; BBDown for anti-scraping, yt-dlp + cookies for paid content
- **YouTube** — shorts, playlists, livestreams, member-only, age-restricted
- 1000+ more via yt-dlp

## CLI

```bash
python video_downloader.py <URL> [options]
python video_downloader.py "..." --no-sponsor --split-chapters
python video_downloader.py "..." --cookies-from-browser chrome
python video_downloader.py "..." --extract-gif --gif-start 30 --gif-duration 5
python video_downloader.py "..." --extract-frames --frame-interval 0.5
python video_downloader.py "..." --sub-translate zh --subtitles
```

## Error Handling

Handles: invalid URLs, network issues, missing deps, age-restricted/geo-blocked content, Bilibili anti-scraping, cookie decryption failures.
