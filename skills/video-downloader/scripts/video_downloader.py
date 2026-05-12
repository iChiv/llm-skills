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
from pathlib import Path


def get_desktop_path():
    """Get the user's Desktop path."""
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        # Fallback to home directory if Desktop doesn't exist
        desktop = Path.home()
    return str(desktop)


def get_bbdown_path():
    """Get the BBDown executable path."""
    # Check in .claude/tools directory
    bbdown_path = Path.home() / '.claude' / 'tools' / 'BBDown' / 'BBDown.exe'
    if bbdown_path.exists():
        return str(bbdown_path)

    # Check if BBDown is in PATH
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
    """
    Build BBDown command for Bilibili videos.

    Args:
        url: Video URL
        output_dir: Output directory (defaults to Desktop)
        quality: Video quality

    Returns:
        List of command arguments
    """
    bbdown_path = get_bbdown_path()
    if not bbdown_path:
        return None

    cmd = [bbdown_path]

    # Add URL first
    cmd.append(url)

    # Work directory
    if output_dir is None:
        output_dir = get_desktop_path()
    cmd.extend(['--work-dir', output_dir])

    # Quality selection (BBDown uses -q for dfn-priority)
    # Note: BBDown quality names are in Chinese
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
                        rate_limit=None):
    """
    Build yt-dlp command with specified options.

    Args:
        url: Video URL
        output_dir: Output directory (defaults to Desktop)
        quality: Video quality ('best', '1080', '720', '480', 'worst')
        audio_only: Download audio only
        format: Preferred format ('mp4', 'webm', 'mkv', etc.)
        playlist: Download entire playlist
        subtitles: Download subtitles
        thumbnail: Embed thumbnail
        concurrent_fragments: Number of concurrent fragments (None=default, e.g. 4)
        cookies_from_browser: Browser to extract cookies from ('chrome', 'firefox', 'edge', etc.)
        live_from_start: Download livestream from the beginning
        rate_limit: Download speed limit (e.g. '1M', '500K', None=unlimited)

    Returns:
        List of command arguments
    """
    cmd = ['yt-dlp']

    # Output directory
    if output_dir is None:
        output_dir = get_desktop_path()
    cmd.extend(['-o', os.path.join(output_dir, '%(title)s.%(ext)s')])

    # Format selection
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
        # Specific quality (e.g., '1080', '720')
        if format:
            cmd.extend(['-f', f'bestvideo[height<={quality}][ext={format}]+bestaudio/best'])
        else:
            cmd.extend(['-f', f'bestvideo[height<={quality}]+bestaudio/best'])

    # Merge format
    if not audio_only:
        cmd.extend(['--merge-output-format', format if format else 'mp4'])

    # Subtitles
    if subtitles:
        cmd.extend(['--sub-langs', 'all', '--write-subs', '--write-auto-subs'])

    # Thumbnail
    if thumbnail:
        cmd.append('--embed-thumbnail')

    # Playlist handling
    if not playlist:
        cmd.append('--no-playlist')

    # Concurrent fragments for faster downloads
    if concurrent_fragments:
        cmd.extend(['--concurrent-fragments', str(concurrent_fragments)])

    # Cookies from browser (convenient authentication)
    if cookies_from_browser:
        cmd.extend(['--cookies-from-browser', cookies_from_browser])

    # Live stream from start
    if live_from_start:
        cmd.append('--live-from-start')

    # Rate limit
    if rate_limit:
        cmd.extend(['--limit-rate', rate_limit])

    # Add URL
    cmd.append(url)

    return cmd


def download_with_bbdown(url, output_dir=None, quality='best'):
    """
    Download a Bilibili video using BBDown.

    Args:
        url: Video URL
        output_dir: Output directory (defaults to Desktop)
        quality: Video quality

    Returns:
        Tuple of (success: bool, message: str, output_path: str or None)
    """
    bbdown_path = get_bbdown_path()
    if not bbdown_path:
        return False, "BBDown not found. Please install BBDown first.", None

    cmd = build_bbdown_command(url, output_dir, quality)
    if not cmd:
        return False, "Failed to build BBDown command", None

    try:
        print(f"Downloading Bilibili video with BBDown...")
        print(f"Output directory: {output_dir or get_desktop_path()}")
        print(f"Quality: {quality}")
        print("-" * 60)

        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            return True, "Bilibili video downloaded successfully!", None
        else:
            return False, f"BBDownload failed with exit code {result.returncode}", None

    except KeyboardInterrupt:
        return False, "Download interrupted by user", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def download_video(url, output_dir=None, quality='best', audio_only=False,
                   format=None, playlist=False, subtitles=False,
                   thumbnail=False, use_bbdown=None,
                   concurrent_fragments=None, cookies_from_browser=None,
                   live_from_start=False, rate_limit=None):
    """
    Download a video using yt-dlp or BBDown (for Bilibili).

    Args:
        url: Video URL
        output_dir: Output directory (defaults to Desktop)
        quality: Video quality ('best', '1080', '720', '480', 'worst')
        audio_only: Download audio only
        format: Preferred format ('mp4', 'webm', 'mkv', etc.)
        playlist: Download entire playlist
        subtitles: Download subtitles
        thumbnail: Embed thumbnail
        use_bbdown: Force use of BBDown (None = auto-detect)
        concurrent_fragments: Number of concurrent fragments for faster download
        cookies_from_browser: Browser to extract cookies from ('chrome', 'firefox', etc.)
        live_from_start: Download livestream from the beginning
        rate_limit: Download speed limit (e.g. '1M', '500K')

    Returns:
        Tuple of (success: bool, message: str, output_path: str or None)
    """
    # Auto-detect Bilibili URLs
    if use_bbdown is None:
        use_bbdown = is_bilibili_url(url)

    # Use BBDown for Bilibili
    if use_bbdown:
        print(f"Detected Bilibili URL, using BBDown...")
        return download_with_bbdown(url, output_dir, quality)

    # Check if yt-dlp is available
    if not shutil.which('yt-dlp'):
        return False, "Error: yt-dlp is not installed or not in PATH", None

    # Check ffmpeg availability (needed for merging and post-processing)
    if not shutil.which('ffmpeg'):
        print("Warning: ffmpeg not found in PATH. Post-processing (merging, format conversion) may fail.")
        print("Download ffmpeg from: https://www.gyan.dev/ffmpeg/builds/")
        print("Or: https://github.com/BtbN/FFmpeg-Builds/releases")

    # Build command
    cmd = build_ytdlp_command(
        url=url,
        output_dir=output_dir,
        quality=quality,
        audio_only=audio_only,
        format=format,
        playlist=playlist,
        subtitles=subtitles,
        thumbnail=thumbnail,
        concurrent_fragments=concurrent_fragments,
        cookies_from_browser=cookies_from_browser,
        live_from_start=live_from_start,
        rate_limit=rate_limit
    )

    # Execute download
    try:
        print(f"Downloading from: {url}")
        print(f"Output directory: {output_dir or get_desktop_path()}")
        print(f"Quality: {quality}")
        if audio_only:
            print("Audio only: Yes")
        print("-" * 60)

        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            return True, "Download completed successfully!", None
        else:
            return False, f"Download failed with exit code {result.returncode}", None

    except KeyboardInterrupt:
        return False, "Download interrupted by user", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("Usage: python video_downloader.py <URL> [options]")
        print("\nOptions:")
        print("  --quality <best|1080|720|480|worst>  Video quality (default: best)")
        print("  --audio-only                        Download audio only")
        print("  --format <mp4|webm|mkv>             Preferred format")
        print("  --playlist                          Download entire playlist")
        print("  --subtitles                         Download subtitles")
        print("  --thumbnail                         Embed thumbnail")
        print("  --output-dir <path>                 Output directory")
        print("  --use-bbdown                        Force use BBDown")
        print("  --concurrent-fragments <N>          Concurrent fragments (e.g. 4)")
        print("  --cookies-from-browser <browser>    Use browser cookies (chrome/firefox/edge)")
        print("  --live-from-start                   Download livestream from start")
        print("  --rate-limit <speed>                Limit download speed (e.g. 1M, 500K)")
        sys.exit(1)

    url = sys.argv[1]

    # Parse options (simple implementation)
    quality = 'best'
    audio_only = False
    format = None
    playlist = False
    subtitles = False
    thumbnail = False
    output_dir = None
    use_bbdown = None
    concurrent_fragments = None
    cookies_from_browser = None
    live_from_start = False
    rate_limit = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--quality' and i + 1 < len(sys.argv):
            quality = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--audio-only':
            audio_only = True
            i += 1
        elif sys.argv[i] == '--format' and i + 1 < len(sys.argv):
            format = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--playlist':
            playlist = True
            i += 1
        elif sys.argv[i] == '--subtitles':
            subtitles = True
            i += 1
        elif sys.argv[i] == '--thumbnail':
            thumbnail = True
            i += 1
        elif sys.argv[i] == '--output-dir' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--use-bbdown':
            use_bbdown = True
            i += 1
        elif sys.argv[i] == '--concurrent-fragments' and i + 1 < len(sys.argv):
            concurrent_fragments = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--cookies-from-browser' and i + 1 < len(sys.argv):
            cookies_from_browser = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--live-from-start':
            live_from_start = True
            i += 1
        elif sys.argv[i] == '--rate-limit' and i + 1 < len(sys.argv):
            rate_limit = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    success, message, _ = download_video(
        url=url,
        output_dir=output_dir,
        quality=quality,
        audio_only=audio_only,
        format=format,
        playlist=playlist,
        subtitles=subtitles,
        thumbnail=thumbnail,
        use_bbdown=use_bbdown,
        concurrent_fragments=concurrent_fragments,
        cookies_from_browser=cookies_from_browser,
        live_from_start=live_from_start,
        rate_limit=rate_limit
    )

    print("\n" + "=" * 60)
    print(message)
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
