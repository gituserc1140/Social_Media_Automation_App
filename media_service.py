"""Local audio/video helpers."""

import math
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg


def convert_to_tiktok_format(video_bytes: bytes, zoom: float = 1.0) -> bytes:
    """Fit a video over a sampled solid background in TikTok's 1080x1920 format."""
    if not math.isfinite(zoom) or not 0.5 <= zoom <= 2.0:
        raise ValueError("Video zoom must be between 0.5 and 2.0.")

    with tempfile.TemporaryDirectory(prefix="pixel-post-media-") as temp_dir:
        video_path = Path(temp_dir) / "video.mp4"
        output_path = Path(temp_dir) / "tiktok-video.mp4"
        video_path.write_bytes(video_bytes)
        sample_command = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-i",
            str(video_path),
            "-vf",
            "scale=1:1:flags=area,format=rgb24",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "pipe:1",
        ]
        try:
            sample = subprocess.run(
                sample_command,
                check=True,
                capture_output=True,
                timeout=30,
            ).stdout
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"Could not sample the video background color: {details[-1000:]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("Sampling the video background color exceeded 30 seconds.") from exc
        if len(sample) != 3:
            raise ValueError("Could not read a video frame to sample its background color.")
        background_color = "".join(f"{channel:02x}" for channel in sample)
        zoom_text = f"{zoom:.2f}"
        video_filter = (
            "[0:v]null[foreground];"
            f"[foreground]scale=1080*{zoom_text}:1920*{zoom_text}:"
            "force_original_aspect_ratio=decrease[foreground];"
            f"color=c=0x{background_color}:s=1080x1920:r=30[background];"
            "[background][foreground]overlay=(W-w)/2:(H-h)/2:shortest=1,"
            "setsar=1,format=yuv420p[video]"
        )
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-i",
            str(video_path),
            "-map",
            "[video]",
            "-map",
            "0:a?",
            "-filter_complex",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=600)
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"Could not convert the video to TikTok format: {details[-1000:]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                "Converting the video to TikTok format exceeded the 10-minute limit."
            ) from exc
        return output_path.read_bytes()


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
