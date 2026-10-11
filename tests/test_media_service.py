import re
import subprocess

import imageio_ffmpeg

import media_service


def test_convert_to_tiktok_format_outputs_1080_by_1920_and_keeps_audio(tmp_path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    source_path = tmp_path / "source.mp4"
    source = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=640x360:d=0.25",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=0.25",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(source_path),
        ],
        check=True,
        capture_output=True,
    )
    assert source.returncode == 0

    converted = media_service.convert_to_tiktok_format(source_path.read_bytes())
    output_path = tmp_path / "converted.mp4"
    output_path.write_bytes(converted)

    probe = subprocess.run(
        [ffmpeg, "-i", str(output_path), "-frames:v", "1", "-f", "null", "-"],
        check=True,
        capture_output=True,
    )
    output_info = probe.stderr.decode("utf-8", errors="replace")
    assert re.search(r"\b1080x1920\b", output_info)

    corner = subprocess.run(
        [
            ffmpeg,
            "-i",
            str(output_path),
            "-vf",
            "crop=2:2:0:0,format=rgb24",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    ).stdout
    assert len(corner) == 12
    assert corner[0] > 200 and corner[1] < 60 and corner[2] < 60

    audio = subprocess.run(
        [ffmpeg, "-i", str(output_path), "-map", "0:a:0", "-f", "null", "-"],
        check=True,
        capture_output=True,
    )
    assert audio.returncode == 0
