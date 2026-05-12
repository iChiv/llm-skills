#!/usr/bin/env python3
"""
Video Downloader - Wrapper for yt-dlp and BBDown
Downloads videos from YouTube, Bilibili, Vimeo, and 1000+ other websites.
"""

import os
import sys
import subprocess
import shutil
import re
import json
import tempfile
from pathlib import Path


def get_desktop_path():
    """Get the user's Desktop path."""
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home()
    return str(desktop)


def get_bbdown_path():
    """Get the BBDown executable path."""
    bbdown_path = Path.home() / '.claude' / 'tools' / 'BBDown' / 'BBDown.exe'
    if bbdown_path.exists():
        return str(bbdown_path)
    bbdown_in_path = shutil.which('BBDown.exe')
    if bbdown_in_path:
        return bbdown_in_path
    return None


def is_bilibili_url(url):
    """Check if the URL is from Bilibili."""
    bilibili_patterns = [
        r'bilibili\.com/video',
        r'b23\.tv',
        r'bilibili\.com/bangumi',
    ]
    return any(re.search(pattern, url) for pattern in bilibili_patterns)


def build_bbdown_command(url, output_dir=None, quality='best'):
    """Build BBDown command for Bilibili videos."""
    bbdown_path = get_bbdown_path()
    if not bbdown_path:
        return None

    cmd = [bbdown_path]
    cmd.append(url)

    if output_dir is None:
        output_dir = get_desktop_path()
    cmd.extend(['--work-dir', output_dir])

    quality_map = {
        'best': '8K 超高清, 1080P 高码率, HDR 视界',
        '1080': '1080P 高码率',
        '720': '720P 高码率',
        '480': '480P 清晰',
        'worst': '360P 流畅'
    }
    q = quality_map.get(quality, '8K 超高清, 1080P 高码率, HDR 视界')
    cmd.extend(['-q', q])

    return cmd


def build_ytdlp_command(url, output_dir=None, quality='best', audio_only=False,
                        format=None, playlist=False, subtitles=False,
                        thumbnail=False, concurrent_fragments=None,
                        cookies_from_browser=None, live_from_start=False,
                        rate_limit=None, no_sponsor=False,
                        split_chapters=False, info_only=False,
                        list_formats=False, download_archive=None,
                        batch_file=None, organize=False,
                        recode=None, sub_translate=None):
    """Build yt-dlp command with specified options."""
    cmd = ['yt-dlp']

    if output_dir is None:
        output_dir = get_desktop_path()

    if organize:
        template = os.path.join(output_dir, '%(extractor)s', '%(uploader)s', '%(title)s.%(ext)s')
    else:
        template = os.path.join(output_dir, '%(title)s.%(ext)s')
    cmd.extend(['-o', template])

    if audio_only:
        cmd.extend(['-x', '--audio-format', 'mp3'])
    elif quality == 'best':
        if format:
            cmd.extend(['-f', f'bestvideo[ext={format}]+bestaudio/best'])
        else:
            cmd.extend(['-f', 'bestvideo+bestaudio/best'])
    elif quality == 'worst':
        cmd.extend(['-f', 'worst'])
    else:
        if format:
            cmd.extend(['-f', f'bestvideo[height<={quality}][ext={format}]+bestaudio/best'])
        else:
            cmd.extend(['-f', f'bestvideo[height<={quality}]+bestaudio/best'])

    if not playlist:
        cmd.append('--no-playlist')

    if subtitles:
        cmd.extend(['--write-subs', '--write-auto-subs', '--embed-subs'])
    if sub_translate:
        cmd.extend(['--sub-langs', f'{sub_translate}.*', '--write-subs', '--write-auto-subs'])
        if subtitles:
            cmd.append('--embed-subs')

    if thumbnail:
        cmd.extend(['--embed-thumbnail'])

    if no_sponsor:
        cmd.extend(['--sponsorblock-mark', 'all'])

    if split_chapters:
        cmd.extend(['--split-chapters'])

    if info_only:
        cmd.extend(['--dump-json'])
    if list_formats:
        cmd.extend(['--list-formats'])

    if download_archive:
        cmd.extend(['--download-archive', download_archive])

    if batch_file:
        cmd.extend(['--batch-file', batch_file])

    if recode:
        cmd.extend(['--recode-video', recode])

    if concurrent_fragments:
        cmd.extend(['--concurrent-fragments', str(concurrent_fragments)])
    if cookies_from_browser:
        cmd.extend(['--cookies-from-browser', cookies_from_browser])
    if live_from_start:
        cmd.extend(['--live-from-start'])
    if rate_limit:
        cmd.extend(['--limit-rate', rate_limit])

    cmd.append('--no-progress')
    cmd.append(url)
    return cmd


def _find_downloaded_file(output_dir, base_stem):
    """Find the downloaded video file by matching stem."""
    for ext in ('.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.opus', '.flv'):
        p = Path(output_dir) / (base_stem + ext)
        if p.exists():
            return p
    return None


def extract_gif(video_path, start=0, duration=5, fps=10, width=480):
    """Extract a GIF from a video file using ffmpeg."""
    output = Path(video_path).with_suffix('.gif')
    palette = tempfile.mktemp(suffix='.png')

    cmd_palette = [
        'ffmpeg', '-y', '-ss', str(start), '-t', str(duration),
        '-i', str(video_path),
        '-vf', f'fps={fps},scale={width}:-1:flags=lanczos,palettegen',
        str(palette)
    ]
    subprocess.run(cmd_palette, capture_output=True)

    cmd_gif = [
        'ffmpeg', '-y', '-ss', str(start), '-t', str(duration),
        '-i', str(video_path), '-i', str(palette),
        '-lavfi', f'fps={fps},scale={width}:-1:flags=lanczos [x]; [x][1:v] paletteuse',
        str(output)
    ]
    result = subprocess.run(cmd_gif, capture_output=True)

    if Path(palette).exists():
        Path(palette).unlink()

    if result.returncode == 0 and output.exists():
        return str(output)
    return None


def extract_frames(video_path, output_dir, interval=1.0):
    """Extract frames from a video at regular intervals."""
    stem = Path(video_path).stem
    pattern = os.path.join(output_dir, f'{stem}_frame_%04d.png')
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-vf', f'fps=1/{interval}',
        str(pattern)
    ]
    subprocess.run(cmd, capture_output=True)

    frames = sorted(Path(output_dir).glob(f'{stem}_frame_*.png'))
    return [str(f) for f in frames]


def _parse_ytdlp_json_output(stdout):
    """Parse JSON lines from yt-dlp --dump-json output."""
    results = []
    for line in stdout.strip().splitlines():
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return results


def download_video(url, output_dir=None, quality='best', audio_only=False,
                   format=None, playlist=False, subtitles=False,
                   thumbnail=False, use_bbdown=None,
                   concurrent_fragments=None, cookies_from_browser=None,
                   live_from_start=False, rate_limit=None,
                   no_sponsor=False, split_chapters=False,
                   info_only=False, list_formats=False,
                   download_archive=None, batch_file=None,
                   organize=False, recode=None, sub_translate=None,
                   extract_gif_enabled=False, gif_start=0, gif_duration=5,
                   gif_fps=10, gif_width=480,
                   extract_frames_enabled=False, frame_interval=1.0):
    """
    Download a video from a supported platform.

    Returns:
        tuple: (success: bool, message: str, extra: dict | None)
    """
    if output_dir is None:
        output_dir = get_desktop_path()

    os.makedirs(output_dir, exist_ok=True)

    force_bbdown = (use_bbdown is True)
    auto_bbdown = (use_bbdown is None and is_bilibili_url(url))

    if force_bbdown or auto_bbdown:
        cmd = build_bbdown_command(url, output_dir, quality)
        if cmd:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        encoding='utf-8', errors='replace')
                if result.returncode == 0:
                    return True, "Downloaded successfully with BBDown!", None
                return False, f"BBDown failed (code {result.returncode}): {result.stderr[:500]}", None
            except Exception as e:
                return False, f"BBDown error: {e}", None
        return False, "BBDown not found. Install from https://github.com/nilaoda/BBDown", None

    cmd = build_ytdlp_command(
        url, output_dir, quality, audio_only,
        format, playlist, subtitles, thumbnail,
        concurrent_fragments, cookies_from_browser,
        live_from_start, rate_limit,
        no_sponsor, split_chapters,
        info_only, list_formats,
        download_archive, batch_file,
        organize, recode, sub_translate
    )

    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding='utf-8', errors='replace')

        if info_only:
            data = _parse_ytdlp_json_output(result.stdout)
            if data:
                return True, f"Retrieved info for {len(data)} video(s)", {"json": data}
            return True, "Info retrieved (empty)", {"json": []}

        if list_formats:
            return True, result.stdout, None

        if result.returncode != 0:
            return False, f"Download failed (code {result.returncode}): {result.stderr[:500]}", None

        downloaded_file = None
        for line in reversed(result.stdout.splitlines()):
            if 'Destination:' in line:
                candidate = line.split('Destination:', 1)[-1].strip()
                candidate_path = Path(candidate)
                if candidate_path.exists():
                    downloaded_file = candidate_path
                    break
            if 'Merging formats into' in line:
                candidate = line.split('into', 1)[-1].strip().strip('"')
                candidate_path = Path(candidate)
                if candidate_path.exists():
                    downloaded_file = candidate_path
                    break

        extra = {}

        if extract_gif_enabled and downloaded_file:
            gif_path = extract_gif(str(downloaded_file),
                                   start=gif_start, duration=gif_duration,
                                   fps=gif_fps, width=gif_width)
            if gif_path:
                extra['gif_path'] = gif_path

        if extract_frames_enabled and downloaded_file:
            frames = extract_frames(str(downloaded_file), output_dir,
                                    interval=frame_interval)
            if frames:
                extra['frame_paths'] = frames

        if extra:
            return True, f"Downloaded + post-processing complete", extra
        return True, "Download completed successfully!", None

    except KeyboardInterrupt:
        return False, "Download interrupted by user", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def main():
    if len(sys.argv) < 2:
        print("Usage: python video_downloader.py <URL> [options]")
        print()
        print("=== Download options ===")
        print("  --quality <best|1080|720|480|worst>")
        print("  --audio-only")
        print("  --format <mp4|webm|mkv>")
        print("  --playlist")
        print("  --output-dir <path>")
        print("  --use-bbdown")
        print()
        print("=== Metadata & quality-of-life ===")
        print("  --subtitles                   Download subtitles")
        print("  --sub-translate <lang>        Translate subtitles (e.g. zh, en)")
        print("  --thumbnail                   Embed thumbnail")
        print("  --no-sponsor                  Skip sponsor segments via SponsorBlock")
        print("  --split-chapters              Split output by video chapters")
        print("  --organize                    Auto-sort into platform/channel folders")
        print("  --download-archive <file>     Skip already-downloaded URLs")
        print("  --batch-file <file>           Download URLs from a text file")
        print()
        print("=== Inspection (no download) ===")
        print("  --info                        Print video metadata as JSON")
        print("  --list-formats                List available formats")
        print()
        print("=== Post-processing ===")
        print("  --recode <fmt>                Re-encode to mp4/mkv/webm after download")
        print("  --extract-gif                 Extract a GIF from the video")
        print("  --gif-start <seconds>         GIF start time (default: 0)")
        print("  --gif-duration <seconds>      GIF duration (default: 5)")
        print("  --gif-fps <N>                 GIF frame rate (default: 10)")
        print("  --gif-width <pixels>          GIF width (default: 480)")
        print("  --extract-frames              Extract frames at regular intervals")
        print("  --frame-interval <seconds>    Frame interval (default: 1.0)")
        print()
        print("=== Performance ===")
        print("  --concurrent-fragments <N>")
        print("  --cookies-from-browser <browser>")
        print("  --live-from-start")
        print("  --rate-limit <speed>")
        sys.exit(1)

    url = sys.argv[1]
    args = {
        'url': url,
        'quality': 'best',
        'audio_only': False,
        'format': None,
        'playlist': False,
        'subtitles': False,
        'thumbnail': False,
        'output_dir': None,
        'use_bbdown': None,
        'concurrent_fragments': None,
        'cookies_from_browser': None,
        'live_from_start': False,
        'rate_limit': None,
        'no_sponsor': False,
        'split_chapters': False,
        'info_only': False,
        'list_formats': False,
        'download_archive': None,
        'batch_file': None,
        'organize': False,
        'recode': None,
        'sub_translate': None,
        'extract_gif_enabled': False,
        'gif_start': 0,
        'gif_duration': 5,
        'gif_fps': 10,
        'gif_width': 480,
        'extract_frames_enabled': False,
        'frame_interval': 1.0,
    }

    param_map = {
        '--quality': ('quality', str),
        '--audio-only': ('audio_only', 'flag'),
        '--format': ('format', str),
        '--playlist': ('playlist', 'flag'),
        '--subtitles': ('subtitles', 'flag'),
        '--thumbnail': ('thumbnail', 'flag'),
        '--output-dir': ('output_dir', str),
        '--use-bbdown': ('use_bbdown', 'flag'),
        '--concurrent-fragments': ('concurrent_fragments', int),
        '--cookies-from-browser': ('cookies_from_browser', str),
        '--live-from-start': ('live_from_start', 'flag'),
        '--rate-limit': ('rate_limit', str),
        '--no-sponsor': ('no_sponsor', 'flag'),
        '--split-chapters': ('split_chapters', 'flag'),
        '--info': ('info_only', 'flag'),
        '--list-formats': ('list_formats', 'flag'),
        '--download-archive': ('download_archive', str),
        '--batch-file': ('batch_file', str),
        '--organize': ('organize', 'flag'),
        '--recode': ('recode', str),
        '--sub-translate': ('sub_translate', str),
        '--extract-gif': ('extract_gif_enabled', 'flag'),
        '--gif-start': ('gif_start', float),
        '--gif-duration': ('gif_duration', float),
        '--gif-fps': ('gif_fps', int),
        '--gif-width': ('gif_width', int),
        '--extract-frames': ('extract_frames_enabled', 'flag'),
        '--frame-interval': ('frame_interval', float),
    }

    i = 2
    while i < len(sys.argv):
        flag = sys.argv[i]
        if flag in param_map:
            key, typ = param_map[flag]
            if typ == 'flag':
                args[key] = True
                i += 1
            else:
                if i + 1 < len(sys.argv):
                    args[key] = typ(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1
        else:
            i += 1

    success, message, extra = download_video(**args)

    print("\n" + "=" * 60)
    print(message)
    if extra:
        if 'gif_path' in extra:
            print(f"GIF saved: {extra['gif_path']}")
        if 'frame_paths' in extra:
            print(f"Frames extracted: {len(extra['frame_paths'])} files")
        if 'json' in extra:
            for item in extra['json'][:5]:
                print(f"  - {item.get('title', '?')}  [{item.get('duration', '?')}s]  "
                      f"{item.get('webpage_url', '')}")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
