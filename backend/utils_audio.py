import os
import subprocess
import time
import json
from typing import Optional
import shutil

# Resolve ffmpeg path once at module import time
FFMPEG_EXE = None
FFPROBE_EXE = None

# 1. Try to find ffmpeg in system PATH first (user preference)
FFMPEG_EXE = shutil.which("ffmpeg")
FFPROBE_EXE = shutil.which("ffprobe")

if FFMPEG_EXE:
    print(f"Found system ffmpeg: {FFMPEG_EXE}")
else:
    # 2. Try to use imageio-ffmpeg as fallback
    try:
        import imageio_ffmpeg
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
        print(f" Resolved imageio-ffmpeg: {FFMPEG_EXE}")
    except Exception:
        pass

if FFMPEG_EXE and not FFPROBE_EXE:
    # Derive ffprobe path from ffmpeg path
    ffprobe_candidate = FFMPEG_EXE.replace("ffmpeg.EXE", "ffprobe.EXE").replace("ffmpeg.exe", "ffprobe.exe").replace("ffmpeg", "ffprobe")
    if os.path.exists(ffprobe_candidate):
        FFPROBE_EXE = ffprobe_candidate
        print(f"Found ffprobe: {FFPROBE_EXE}")

if not FFMPEG_EXE:
    print("WARNING: ffmpeg not found anywhere!")


def _get_audio_duration(audio_path: str) -> float:
    """Returns duration in seconds of a WAV/audio file using ffprobe."""
    probe = FFPROBE_EXE or shutil.which("ffprobe")
    if not probe:
        # If ffprobe is not available, skip duration check and assume audio is valid
        print("[utils_audio] ffprobe not found, skipping duration check")
        return 999.0  # Assume valid

    try:
        result = subprocess.run(
            [probe, "-v", "quiet", "-print_format", "json", "-show_streams", audio_path],
            capture_output=True, text=True, timeout=15
        )
        info = json.loads(result.stdout)
        for stream in info.get("streams", []):
            dur = float(stream.get("duration", 0))
            if dur > 0:
                return dur
    except Exception as e:
        print(f"[utils_audio] ffprobe check failed: {e}")
        # If ffprobe fails, skip duration check
        return 999.0
    return 0.0


def extract_audio_from_video(video_path: str) -> Optional[str]:
    """
    Extracts audio from a video file using ffmpeg.
    Returns the path to the extracted audio file (WAV format).
    Optimized for Whisper (16kHz mono).
    """
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return None

    if not FFMPEG_EXE or not os.path.exists(FFMPEG_EXE):
        print(f"ffmpeg executable not found")
        return None

    # Check video file size
    video_size = os.path.getsize(video_path)
    if video_size > 100 * 1024 * 1024:  # 100MB
        print(f"Warning: Large video file ({video_size / (1024*1024):.1f}MB). Audio extraction may take time.")

    # Create a temporary audio file
    audio_dir = os.path.join(os.path.dirname(video_path), "audio")
    os.makedirs(audio_dir, exist_ok=True)

    audio_filename = os.path.splitext(os.path.basename(video_path))[0] + ".wav"
    audio_path = os.path.join(audio_dir, audio_filename)

    print(f"Extracting audio from: {os.path.basename(video_path)} ...")

    # Use ffmpeg to extract audio optimized for Whisper
    cmd = [
        FFMPEG_EXE,
        "-i", video_path,
        "-vn",                   # No video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",          # 16kHz sample rate
        "-ac", "1",              # Mono
        "-y",                    # Overwrite output file if exists
        audio_path
    ]

    try:
        # Run ffmpeg — do NOT use check=True because ffmpeg writes info to stderr
        # which can be misinterpreted as errors
        result = subprocess.run(cmd, capture_output=True, timeout=300)

        # Check if the output file was actually created — that's the real success indicator
        # ffmpeg return code 0 = success, but we also verify file exists
        if result.returncode != 0:
            stderr_text = result.stderr.decode(errors='replace') if result.stderr else ''
            print(f"FFMPEG returned exit code {result.returncode}")
            print(f"FFMPEG stderr: {stderr_text[-500:]}")
            # Even if returncode is non-zero, check if file was created anyway
            if not os.path.exists(audio_path):
                return None

        # Give the OS a moment to flush the file to disk
        time.sleep(0.5)

        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            if file_size > 1000:  # At least 1KB for a real audio file
                # Check audio duration to catch empty/silent audio
                duration = _get_audio_duration(audio_path)
                if duration > 0.1:
                    print(f" Audio extracted successfully ({file_size} bytes, {duration:.1f}s)")
                    return audio_path
                else:
                    print(f"ERROR: Extracted audio has zero duration — video may have no audio track.")
                    return None
            else:
                print(f"ERROR: Extracted audio file is too small ({file_size} bytes)")
                return None
        else:
            print(f" ERROR: Audio file was not created at {audio_path}")
            return None

    except subprocess.TimeoutExpired:
        print(f"ERROR: ffmpeg timed out after 300 seconds")
        return None
    except Exception as e:
        print(f"Unexpected error during audio extraction: {e}")
        return None
