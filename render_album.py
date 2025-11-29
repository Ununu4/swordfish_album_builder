"""
CLI tool to build a single cover video from a directory of WAVs using GPU (NVENC).

Workflow:
1) Transcode each WAV (by filename order) to 24-bit/48k FLAC to normalize formats.
2) Concatenate the FLACs (stream copy) into one FLAC.
3) Render a still-image video with the cover art and the concatenated audio using NVENC (YouTube-friendly).

Usage:
  python render_album.py --input "C:\\path\\to\\album" --cover cover.png --output FULL-GPU.mp4

Requirements:
  - ffmpeg on PATH (with NVENC support)
  - NVIDIA GPU for h264_nvenc
"""

import argparse
import sys
import tempfile
from pathlib import Path
import shutil
import subprocess

FRAMERATE = 30  # higher fps to show cover immediately and align with audio end


def run(cmd):
    """Run a command, raise on failure, return stdout+stderr."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout}")
    return proc.stdout


def ensure_exists(path: Path, kind: str):
    if not path.exists():
        raise FileNotFoundError(f"Missing {kind}: {path}")


def transcode_wavs_to_flacs(wavs, workdir: Path):
    """Transcode each WAV to 24-bit/48k FLAC; return list of FLAC paths and list file path."""
    flac_paths = []
    list_path = workdir / "flac_list.txt"
    list_path.write_text("", encoding="utf-8")
    for idx, wav in enumerate(wavs, start=1):
        flac_out = workdir / f"{idx:02d}.flac"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(wav),
            "-c:a",
            "flac",
            "-sample_fmt",
            "s32",
            "-ar",
            "48000",
            str(flac_out),
        ]
        run(cmd)
        flac_paths.append(flac_out)
        with list_path.open("a", encoding="utf-8") as f:
            f.write(f"file '{flac_out}'\n")
    return flac_paths, list_path


def concat_flacs(list_path: Path, out_flac: Path):
    """Concat normalized FLACs to one FLAC (stream copy)."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c:a",
        "flac",
        "-sample_fmt",
        "s32",
        "-ar",
        "48000",
        str(out_flac),
    ]
    run(cmd)


def render_video(cover: Path, audio: Path, output: Path):
    """
    Render final video with NVENC.
    - If output is MP4, encode audio to AAC 320k (YouTube-friendly).
    - Otherwise, copy audio (assumes FLAC).
    """
    ext = output.suffix.lower()
    audio_codec = ["-c:a", "aac", "-b:a", "320k"] if ext == ".mp4" else ["-c:a", "copy"]
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-framerate",
        str(FRAMERATE),
        "-i",
        str(cover),
        "-i",
        str(audio),
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p7",
        "-rc",
        "vbr_hq",
        "-cq",
        "17",
        "-b:v",
        "8M",
        "-maxrate",
        "12M",
        "-bufsize",
        "24M",
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FRAMERATE),
        *audio_codec,
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(cmd)


def main():
    parser = argparse.ArgumentParser(description="Build a single cover video from WAVs using NVENC.")
    parser.add_argument("--input", "-i", required=True, help="Directory containing WAV files.")
    parser.add_argument("--cover", "-c", default="cover.png", help="Cover image filename (default: cover.png).")
    parser.add_argument("--pattern", default="*.wav", help="Glob pattern for WAV files (default: *.wav).")
    parser.add_argument("--output", "-o", default="FULL-GPU.mp4", help="Output video filename (default: FULL-GPU.mp4).")
    args = parser.parse_args()

    root = Path(args.input).expanduser().resolve()
    ensure_exists(root, "input directory")

    cover = (root / args.cover).resolve()
    ensure_exists(cover, "cover image")

    wavs = sorted(root.glob(args.pattern))
    wavs = [w for w in wavs if w.is_file()]
    if not wavs:
        raise SystemExit("No WAV files found.")

    print(f"Found {len(wavs)} WAV files. Concatenating audio...")
    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        flacs, listfile = transcode_wavs_to_flacs(wavs, workdir)
        concat_flac = workdir / "album_concat.flac"
        concat_flacs(listfile, concat_flac)

        output_video = (root / args.output).resolve()
        print(f"Rendering final video -> {output_video.name}")
        render_video(cover, concat_flac, output_video)

    print("Done.")
    print(f"Output video: {output_video}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
