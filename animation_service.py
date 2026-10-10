"""fal.ai image-to-video integration."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests


FAL_MODEL = "fal-ai/wan-i2v"


def animate_image(image_bytes: bytes, prompt: str, api_key: str) -> bytes:
    """Upload an image to fal.ai, generate a video, and return its bytes.

    fal-client reads credentials from its process environment. Running it in a
    short-lived child process keeps a user's key out of Streamlit's shared
    process environment and out of persistent storage.
    """
    if not api_key:
        raise ValueError("Enter a fal.ai API key to animate an image.")

    with tempfile.TemporaryDirectory(prefix="pixel-post-") as temp_dir:
        image_path = Path(temp_dir) / "pixel-art.png"
        image_path.write_bytes(image_bytes)
        script = (
            "import json, sys, fal_client\n"
            "image_url = fal_client.upload_file(sys.argv[1])\n"
            "result = fal_client.subscribe(sys.argv[2], arguments={"
            "'image_url': image_url, 'prompt': sys.argv[3]})\n"
            "print(json.dumps(result))\n"
        )
        child_env = {**os.environ, "FAL_KEY": api_key}
        try:
            completed = subprocess.run(
                [sys.executable, "-c", script, str(image_path), FAL_MODEL, prompt],
                check=True,
                capture_output=True,
                text=True,
                timeout=1800,
                env=child_env,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("fal.ai video generation exceeded the 30-minute limit.") from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or "fal-client did not return an error description.").strip()
            details = details.replace(api_key, "[redacted]")
            raise RuntimeError(f"fal.ai could not generate the video: {details[-1200:]}") from exc

    result_line = next(
        (line for line in reversed(completed.stdout.splitlines()) if line.strip()),
        "",
    )
    try:
        result = json.loads(result_line)
        video_url = result["video"]["url"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("fal.ai returned a response without a video URL.") from exc

    video_response = requests.get(video_url, timeout=180)
    video_response.raise_for_status()
    return video_response.content
