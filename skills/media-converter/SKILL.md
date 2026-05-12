---
name: media-converter
description: Convert video, audio, and image formats using ffmpeg. Supports video transcoding (MP4/MKV/WebM/AVI), audio conversion (MP3/AAC/FLAC/WAV/OGG), image batch conversion (PNG/JPG/WebP), video compression with two-pass encoding, GIF creation, and media metadata inspection.
tool: ffmpeg
tool_args: -version
tool_upstream: FFmpeg/FFmpeg
---

# Media Converter

Pure ffmpeg wrapper for all media format conversion needs.

## Commands

| Command | Purpose |
|---------|---------|
| `info` | Detailed media metadata (resolution, codec, bitrate, streams) |
| `convert-video` | Transcode video between formats/codecs |
| `compress` | Shrink video file size (CRF or target-size two-pass) |
| `convert-audio` | Convert audio formats, extract clips |
| `extract-audio` | Pull audio track from video |
| `convert-image` | Single image format conversion + resize |
| `batch-images` | Batch convert all images of a format in a directory |
| `make-gif` | Video segment to high-quality GIF |

## Quick Start

```python
import sys
sys.path.insert(0, 'C:/Users/happyelements/.claude/skills/media-converter/scripts')
from media_converter import *

# Inspect
ok, msg, info = get_media_info('video.mp4')
print(msg)

# Convert MKV to MP4 with H.265
ok, msg, out = convert_video('input.mkv', output_format='mp4', codec='libx265', crf=20)

# Compress to ~50MB (two-pass)
ok, msg, out = compress_video('large_video.mp4', target_size_mb=50)

# Extract MP3
ok, msg, out = extract_audio('video.mp4', output_format='mp3', bitrate='320k')

# Batch convert PNGs to WebP
ok, msg, files = batch_convert_images('./images/', input_format='png', output_format='webp')

# GIF from video
ok, msg, out = make_gif('video.mp4', start=10, duration=3, fps=15, width=640)
```

## API

All functions return `(success: bool, message: str, result)`.

- `get_media_info(path)` — result is parsed ffprobe dict
- `convert_video(in, out=None, format='mp4', codec='libx264', crf=23, ...)`
- `compress_video(in, out=None, target_size_mb=None, crf=28, ...)`
- `convert_audio(in, out=None, format='mp3', bitrate='192k', ...)`
- `extract_audio(in, out=None, format='mp3')`
- `convert_image(in, out=None, format='png', quality=90, width=None)`
- `batch_convert_images(dir, from='png', to='webp', quality=80, width=None)` — result is list of paths
- `make_gif(in, out=None, start=0, duration=5, fps=10, width=480)`

## CLI

```bash
python media_converter.py info video.mp4
python media_converter.py convert-video in.mkv out.mp4 --codec libx265 --crf 20
python media_converter.py compress big.mp4 small.mp4 --target 50
python media_converter.py extract-audio video.mp4 audio.mp3 --bitrate 320k
python media_converter.py convert-image photo.png thumb.webp --format webp --quality 85 --width 800
python media_converter.py batch-images ./photos/ --from png --to webp --quality 80
python media_converter.py make-gif clip.mp4 demo.gif --start 5 --duration 3 --fps 15 --width 640
```
