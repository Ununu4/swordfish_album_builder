# Swordfish Album Builder

GPU-assisted CLI for turning a folder of WAVs plus cover art into a single, YouTube-ready cover video. Audio is normalized to 24-bit/48 kHz FLAC, concatenated, and paired with your static cover image while ffmpeg encodes video via NVIDIA NVENC.

## Features
- NVENC-powered `h264` video (fast, GPU-based) with YouTube-friendly flags.
- Audio normalization to 24-bit/48 kHz FLAC before concatenation.
- Still-image video with optional AAC 320k audio for `.mp4`, or FLAC passthrough for other containers.
- Simple CLI: point at a folder containing WAVs and a cover image.

## Requirements
- Python 3.8+
- ffmpeg on your `PATH` **built with NVENC** support.
- NVIDIA GPU + drivers supporting `h264_nvenc`.
- Source folder containing WAV files and a cover image (default `cover.png`).
- Python deps: standard library only (`pip install -r requirements.txt` is a no-op).

Check NVENC availability:
- Windows PowerShell: `ffmpeg -hide_banner -encoders | Select-String nvenc`
- macOS/Linux: `ffmpeg -hide_banner -encoders | grep nvenc`

## Install ffmpeg with NVENC (concise)
- Windows: download an NVENC-enabled build (e.g., Gyan.dev “full” or BtbN), unzip, add `bin` to `PATH`.
- macOS/Linux: use a build that lists `h264_nvenc` in `ffmpeg -encoders` (BtbN static builds work; distro packages vary).
- Verify: `ffmpeg -hide_banner -encoders | Select-String nvenc` (PowerShell) or `... | grep nvenc`.

## Quick start
```bash
python render_album.py --input "C:\path\to\album" --cover cover.png --output FULL-GPU.mp4
```
- WAVs are discovered with the glob pattern `*.wav` (customize with `--pattern`).
- Output video is written into the input folder.

## CLI usage
```
python render_album.py --input PATH [--cover COVER.PNG] [--pattern "*.wav"] [--output FULL-GPU.mp4]
```
- `--input, -i` (required): Directory containing WAV files.
- `--cover, -c` (default `cover.png`): Cover image filename relative to `--input`.
- `--pattern` (default `*.wav`): Glob pattern for WAV discovery.
- `--output, -o` (default `FULL-GPU.mp4`): Output video filename (container sets audio handling).

## How it works
1) Validate inputs and gather WAVs (sorted by filename).
2) Transcode each WAV to 24-bit/48 kHz FLAC in a temp folder.
3) Concatenate the FLACs (stream copy) into one `album_concat.flac`.
4) Render a still-image video:
   - Video: `h264_nvenc`, preset `p7`, `vbr_hq`, `cq 17`, `8M` target, `12M` max, `24M` buffer, `yuv420p`, `+faststart`, 30 fps cover (shows immediately, trims with audio).
   - Audio: AAC 320k for `.mp4`; otherwise audio is stream-copied (FLAC).
5) Clean up temp files and print the output path.

## Examples
- Default MP4 (AAC audio):
  ```bash
  python render_album.py -i "D:\music\album" -c cover.png -o FULL-GPU.mp4
  ```
- MKV with FLAC passthrough:
  ```bash
  python render_album.py -i ~/music/album -c cover.jpg -o album.mkv
  ```
- Custom WAV pattern:
  ```bash
  python render_album.py -i ./album -c art.png --pattern "*_mixdown.wav"
  ```

## Tips & troubleshooting
- Ensure ffmpeg sees NVENC; otherwise, fallback CPU encoders will fail the script.
- If you hit `Missing cover image` or `No WAV files found`, double-check paths relative to `--input`.
- Large albums: keep enough disk space for temp FLACs (created in a temp directory).
- To tweak quality/bitrate, adjust the `render_video` NVENC parameters in `render_album.py`.

## Development
- Install Python requirements: `pip install -r requirements.txt` (no third-party libs; stdlib only).
- Single-file script: `render_album.py`
- License: MIT (see `LICENSE`)

## License
MIT. See `LICENSE`.
