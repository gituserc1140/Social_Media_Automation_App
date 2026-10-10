"""Local audio/video helpers."""

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg


def add_background_music(video_bytes: bytes, music_bytes: bytes, music_extension: str) -> bytes:
    """Mux music under a video, trimming the audio when the video ends."""
    with tempfile.TemporaryDirectory(prefix="pixel-post-media-") as temp_dir:
        video_path = Path(temp_dir) / "video.mp4"
        music_path = Path(temp_dir) / f"music.{music_extension}"
        output_path = Path(temp_dir) / "with-music.mp4"
        video_path.write_bytes(video_bytes)
        music_path.write_bytes(music_bytes)
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(music_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=180)
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Could not add the soundtrack to this video: {details[-1000:]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("Adding the soundtrack exceeded the 3-minute limit.") from exc
        return output_path.read_bytes()
