#!/usr/bin/env python3
"""
Media Converter - ffmpeg wrapper for video/audio/image/GIF conversion.
"""

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_ffmpeg(args, timeout=None):
    result = subprocess.run(
        ['ffmpeg', '-y'] + args,
        capture_output=True, text=True,
        encoding='utf-8', errors='replace',
        timeout=timeout
    )
    return result.returncode, result.stdout, result.stderr


def _run_ffprobe(path):
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', str(path)
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------

def convert_video(input_path, output_path=None, output_format='mp4',
                  codec='libx264', crf=23, preset='medium',
                  resolution=None, bitrate=None, audio_codec='aac',
                  audio_bitrate='128k', fps=None, start=None, duration=None):
    input_path = Path(input_path)
    if not input_path.exists():
        return False, f"Input not found: {input_path}", None

    if output_path is None:
        output_path = input_path.with_suffix(f'.{output_format}')
    output_path = Path(output_path)

    args = []
    if start is not None:
        args.extend(['-ss', str(start)])
    args.extend(['-i', str(input_path)])
    if duration is not None:
        args.extend(['-t', str(duration)])

    if codec != 'copy':
        args.extend(['-c:v', codec, '-crf', str(crf), '-preset', preset])
    else:
        args.extend(['-c:v', 'copy'])

    if resolution:
        args.extend(['-vf', f'scale={resolution}'])
    if bitrate:
        args.extend(['-b:v', bitrate])
    if fps:
        args.extend(['-r', str(fps)])
    if audio_codec:
        args.extend(['-c:a', audio_codec])
    if audio_bitrate and audio_codec != 'copy':
        args.extend(['-b:a', audio_bitrate])

    args.extend(['-movflags', '+faststart'])
    args.append(str(output_path))

    rc, stdout, stderr = _run_ffmpeg(args)

    if rc == 0 and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        return True, f"Converted -> {output_path.name} ({size_mb:.1f} MB)", str(output_path)
    return False, f"ffmpeg error (code {rc}): {stderr[:300]}", None


def compress_video(input_path, output_path=None, target_size_mb=None,
                   crf=28, preset='medium', resolution=None):
    input_path = Path(input_path)
    if not input_path.exists():
        return False, f"Input not found: {input_path}", None

    if output_path is None:
        output_path = input_path.parent / f'{input_path.stem}_compressed.mp4'

    if target_size_mb:
        info = _run_ffprobe(input_path)
        duration_s = float(info['format']['duration']) if info else 0
        if duration_s <= 0:
            return False, "Could not determine video duration", None

        target_bits = (target_size_mb * 8 * 1024 * 1024)
        audio_bits = 128 * 1000
        video_bitrate = int((target_bits / duration_s) - audio_bits)
        video_bitrate = max(video_bitrate, 100000)

        args1 = ['-i', str(input_path), '-c:v', 'libx264',
                 '-b:v', str(video_bitrate), '-preset', preset,
                 '-pass', '1', '-an', '-f', 'null', 'NUL']
        _run_ffmpeg(args1)

        args2 = ['-i', str(input_path), '-c:v', 'libx264',
                 '-b:v', str(video_bitrate), '-preset', preset,
                 '-pass', '2', '-c:a', 'aac', '-b:a', '128k',
                 '-movflags', '+faststart']
        if resolution:
            args2.extend(['-vf', f'scale={resolution}'])
        args2.append(str(output_path))
        rc, stdout, stderr = _run_ffmpeg(args2)

        for f in Path().glob('ffmpeg2pass-*'):
            f.unlink()
    else:
        return convert_video(
            input_path, output_path, output_format='mp4',
            codec='libx264', crf=crf, preset=preset,
            resolution=resolution
        )

    if rc == 0 and Path(output_path).exists():
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        return True, f"Compressed -> {Path(output_path).name} ({size_mb:.1f} MB)", str(output_path)
    return False, f"Compression failed (code {rc}): {stderr[:300]}", None


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def convert_audio(input_path, output_path=None, output_format='mp3',
                  codec='libmp3lame', bitrate='192k', sample_rate=None,
                  start=None, duration=None):
    input_path = Path(input_path)
    if not input_path.exists():
        return False, f"Input not found: {input_path}", None

    if output_path is None:
        output_path = input_path.with_suffix(f'.{output_format}')

    args = []
    if start is not None:
        args.extend(['-ss', str(start)])
    args.extend(['-i', str(input_path)])
    if duration is not None:
        args.extend(['-t', str(duration)])

    args.extend(['-c:a', codec, '-b:a', bitrate])
    if sample_rate:
        args.extend(['-ar', str(sample_rate)])
    args.extend(['-vn'])
    args.append(str(output_path))

    rc, stdout, stderr = _run_ffmpeg(args)

    if rc == 0 and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        return True, f"Converted -> {output_path.name} ({size_mb:.1f} MB)", str(output_path)
    return False, f"ffmpeg error (code {rc}): {stderr[:300]}", None


def extract_audio(input_path, output_path=None, output_format='mp3',
                  bitrate='192k'):
    return convert_audio(input_path, output_path, output_format, bitrate=bitrate)


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

def convert_image(input_path, output_path=None, output_format='png',
                  quality=90, width=None, height=None, keep_aspect=True):
    input_path = Path(input_path)
    if not input_path.exists():
        return False, f"Input not found: {input_path}", None

    if output_path is None:
        output_path = input_path.with_suffix(f'.{output_format}')

    args = ['-i', str(input_path)]

    if width or height:
        if keep_aspect:
            w = str(width) if width else '-1'
            h = str(height) if height else '-1'
            args.extend(['-vf', f'scale={w}:{h}'])
        else:
            w = str(width) if width else 'iw'
            h = str(height) if height else 'ih'
            args.extend(['-vf', f'scale={w}:{h}'])

    args.extend(['-q:v', str(int((100 - quality) / 100 * 31))])
    args.append(str(output_path))

    rc, stdout, stderr = _run_ffmpeg(args)

    if rc == 0 and output_path.exists():
        return True, f"Converted -> {output_path.name}", str(output_path)
    return False, f"ffmpeg error (code {rc}): {stderr[:300]}", None


def batch_convert_images(input_dir, output_dir=None, input_format='png',
                         output_format='webp', quality=80, width=None):
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        return False, f"Directory not found: {input_dir}", None

    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    converted = []
    failed = []

    for f in sorted(input_dir.glob(f'*.{input_format}')):
        out = output_dir / f'{f.stem}.{output_format}'
        ok, msg, _ = convert_image(str(f), str(out), output_format,
                                   quality=quality, width=width)
        if ok:
            converted.append(str(out))
        else:
            failed.append(f.name)

    summary = f"Converted {len(converted)} images"
    if failed:
        summary += f", {len(failed)} failed: {', '.join(failed[:5])}"
    return True, summary, converted


# ---------------------------------------------------------------------------
# GIF
# ---------------------------------------------------------------------------

def make_gif(input_path, output_path=None, start=0, duration=5,
             fps=10, width=480, quality='high'):
    input_path = Path(input_path)
    if not input_path.exists():
        return False, f"Input not found: {input_path}", None

    if output_path is None:
        output_path = input_path.with_suffix('.gif')

    if quality == 'high':
        palette = tempfile.mktemp(suffix='.png')
        _run_ffmpeg([
            '-ss', str(start), '-t', str(duration),
            '-i', str(input_path),
            '-vf', f'fps={fps},scale={width}:-1:flags=lanczos,palettegen',
            str(palette)
        ])
        rc, stdout, stderr = _run_ffmpeg([
            '-ss', str(start), '-t', str(duration),
            '-i', str(input_path), '-i', palette,
            '-lavfi', f'fps={fps},scale={width}:-1:flags=lanczos [x]; [x][1:v] paletteuse',
            str(output_path)
        ])
        if Path(palette).exists():
            Path(palette).unlink()
    else:
        rc, stdout, stderr = _run_ffmpeg([
            '-ss', str(start), '-t', str(duration),
            '-i', str(input_path),
            '-vf', f'fps={fps},scale={width}:-1',
            str(output_path)
        ])

    if rc == 0 and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        return True, f"GIF created -> {output_path.name} ({size_mb:.1f} MB)", str(output_path)
    return False, f"ffmpeg error (code {rc}): {stderr[:300]}", None


# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------

def get_media_info(input_path):
    input_path = Path(input_path)
    if not input_path.exists():
        return False, f"File not found: {input_path}", None

    info = _run_ffprobe(input_path)
    if info is None:
        return False, "Could not read media info", None

    fmt = info.get('format', {})
    streams = info.get('streams', [])

    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']

    lines = [
        f"File: {input_path.name}",
        f"Size: {int(fmt.get('size', 0)) / (1024*1024):.1f} MB",
        f"Duration: {float(fmt.get('duration', 0)):.1f}s",
        f"Format: {fmt.get('format_name', '?')}",
    ]

    for i, vs in enumerate(video_streams):
        lines.append(f"  Video #{i}: {vs.get('codec_name')} "
                     f"{vs.get('width')}x{vs.get('height')} "
                     f"{vs.get('r_frame_rate', '?')}fps "
                     f"bitrate={int(vs.get('bit_rate', 0)) // 1000}kbps")

    for i, a_s in enumerate(audio_streams):
        lines.append(f"  Audio #{i}: {a_s.get('codec_name')} "
                     f"{a_s.get('sample_rate', '?')}Hz "
                     f"{a_s.get('channels', '?')}ch "
                     f"bitrate={int(a_s.get('bit_rate', 0)) // 1000}kbps")

    return True, "\n".join(lines), info


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _usage():
    print("Usage: python media_converter.py <command> [args]")
    print()
    print("Commands:")
    print("  info <file>                        Show media metadata")
    print("  convert-video <in> [out] [opts]    Transcode video")
    print("       --format mp4|mkv|webm|avi     (default: mp4)")
    print("       --codec libx264|libx265|copy  (default: libx264)")
    print("       --crf 18-28                   (default: 23)")
    print("       --resolution WxH              (e.g. 1920x1080)")
    print("       --bitrate 2M")
    print("       --fps 30")
    print("       --start 10 --duration 30")
    print("  compress <in> [out] [opts]         Shrink video file size")
    print("       --target 50                   (target MB)")
    print("       --crf 28                      (default: 28)")
    print("       --resolution 1280:-1")
    print("  convert-audio <in> [out] [opts]    Convert audio")
    print("       --format mp3|aac|flac|wav|ogg (default: mp3)")
    print("       --bitrate 192k                (default: 192k)")
    print("       --start 10 --duration 30")
    print("  extract-audio <in> [out]            Extract audio from video")
    print("  convert-image <in> [out] [opts]     Image format conversion")
    print("       --format png|jpg|webp          (default: png)")
    print("       --quality 80                   (default: 90)")
    print("       --width 800")
    print("  batch-images <dir> [opts]           Batch convert images")
    print("       --from png --to webp")
    print("       --quality 80 --width 800")
    print("  make-gif <video> [out] [opts]       Create GIF from video")
    print("       --start 0 --duration 5")
    print("       --fps 10 --width 480")
    sys.exit(1)


def _parse_kv(args, i):
    opts = {}
    while i < len(args):
        if args[i].startswith('--'):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                opts[key] = args[i + 1]
                i += 2
            else:
                opts[key] = True
                i += 1
        else:
            break
    return opts, i


def main():
    if len(sys.argv) < 2:
        _usage()

    cmd = sys.argv[1]

    if cmd == 'info':
        if len(sys.argv) < 3:
            _usage()
        ok, msg, _ = get_media_info(sys.argv[2])
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'convert-video':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        start_i = 3 if out is None else 4
        opts, _ = _parse_kv(sys.argv, start_i)
        ok, msg, _ = convert_video(
            inp, out,
            output_format=opts.get('format', 'mp4'),
            codec=opts.get('codec', 'libx264'),
            crf=int(opts.get('crf', 23)),
            resolution=opts.get('resolution'),
            bitrate=opts.get('bitrate'),
            fps=int(opts['fps']) if 'fps' in opts else None,
            start=float(opts['start']) if 'start' in opts else None,
            duration=float(opts['duration']) if 'duration' in opts else None,
        )
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'compress':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        start_i = 3 if out is None else 4
        opts, _ = _parse_kv(sys.argv, start_i)
        ok, msg, _ = compress_video(
            inp, out,
            target_size_mb=float(opts['target']) if 'target' in opts else None,
            crf=int(opts.get('crf', 28)),
            resolution=opts.get('resolution'),
        )
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'convert-audio':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        start_i = 3 if out is None else 4
        opts, _ = _parse_kv(sys.argv, start_i)
        fmt = opts.get('format', 'mp3')
        codec_map = {'mp3': 'libmp3lame', 'aac': 'aac', 'flac': 'flac',
                     'wav': 'pcm_s16le', 'ogg': 'libvorbis', 'opus': 'libopus'}
        ok, msg, _ = convert_audio(
            inp, out, output_format=fmt,
            codec=codec_map.get(fmt, 'libmp3lame'),
            bitrate=opts.get('bitrate', '192k'),
            start=float(opts['start']) if 'start' in opts else None,
            duration=float(opts['duration']) if 'duration' in opts else None,
        )
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'extract-audio':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        start_i = 3 if out is None else 4
        opts, _ = _parse_kv(sys.argv, start_i)
        ok, msg, _ = extract_audio(inp, out, opts.get('format', 'mp3'),
                                   bitrate=opts.get('bitrate', '192k'))
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'convert-image':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        start_i = 3 if out is None else 4
        opts, _ = _parse_kv(sys.argv, start_i)
        ok, msg, _ = convert_image(
            inp, out,
            output_format=opts.get('format', 'png'),
            quality=int(opts.get('quality', 90)),
            width=int(opts['width']) if 'width' in opts else None,
        )
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'batch-images':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        opts, _ = _parse_kv(sys.argv, 3)
        ok, msg, _ = batch_convert_images(
            inp,
            input_format=opts.get('from', 'png'),
            output_format=opts.get('to', 'webp'),
            quality=int(opts.get('quality', 80)),
            width=int(opts['width']) if 'width' in opts else None,
        )
        print(msg)
        sys.exit(0 if ok else 1)

    elif cmd == 'make-gif':
        if len(sys.argv) < 3:
            _usage()
        inp = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        start_i = 3 if out is None else 4
        opts, _ = _parse_kv(sys.argv, start_i)
        ok, msg, _ = make_gif(
            inp, out,
            start=float(opts.get('start', 0)),
            duration=float(opts.get('duration', 5)),
            fps=int(opts.get('fps', 10)),
            width=int(opts.get('width', 480)),
        )
        print(msg)
        sys.exit(0 if ok else 1)

    else:
        print(f"Unknown command: {cmd}")
        _usage()


if __name__ == '__main__':
    main()
