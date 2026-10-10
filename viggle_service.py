"""Viggle V1 image-to-video generation."""

import time
from typing import Any

import requests


VIGGLE_API_URL = "https://apis.viggle.ai/v1"
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 60
TERMINAL_STATES = {"ready", "failed", "cancelled"}


class ViggleAPIError(RuntimeError):
    """Viggle API failure with its HTTP status and provider error code."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        super().__init__(f"Viggle API returned HTTP {status_code} ({code}): {message}")


def get_credit_balance(api_key: str) -> float:
    response = requests.get(
        f"{VIGGLE_API_URL}/credits",
        headers=_headers(api_key),
        timeout=30,
    )
    payload = _json_response(response)
    balance = payload.get("balance")
    if not isinstance(balance, (int, float)):
        raise ValueError("Viggle returned a response without a credit balance.")
    return float(balance)


def animate_image(
    image_bytes: bytes,
    prompt: str,
    api_key: str,
    *,
    quality: str = "low",
    duration_seconds: int = 5,
    poll_interval: int = POLL_INTERVAL_SECONDS,
    max_poll_attempts: int = MAX_POLL_ATTEMPTS,
) -> bytes:
    """Create an image-referenced Viggle video and download its MP4."""
    if quality not in {"low", "high"}:
        raise ValueError("Viggle quality must be either low or high.")
    if not 3 <= duration_seconds <= 15:
        raise ValueError("Viggle video duration must be between 3 and 15 seconds.")
    if not prompt.strip():
        raise ValueError("Describe the video motion before generating.")
    if not image_bytes:
        raise ValueError("Provide pixel art to use as a Viggle reference image.")

    create_response = requests.post(
        f"{VIGGLE_API_URL}/videos",
        headers=_headers(api_key),
        data={
            "prompt": prompt.strip(),
            "quality": quality,
            "duration_s": str(duration_seconds),
        },
        files={"reference_image": ("pixel-art.png", image_bytes, "image/png")},
        timeout=120,
    )
    created = _json_response(create_response)
    video_id = created.get("id")
    if not isinstance(video_id, str) or not video_id:
        raise ValueError("Viggle did not return a video ID.")

    for attempt in range(max_poll_attempts):
        if attempt:
            time.sleep(poll_interval)
        response = requests.get(
            f"{VIGGLE_API_URL}/videos/{video_id}",
            headers=_headers(api_key),
            timeout=30,
        )
        video = _json_response(response)
        status = video.get("status")
        if status in TERMINAL_STATES:
            break
    else:
        raise TimeoutError(
            f"Viggle video {video_id} was not ready after {max_poll_attempts} checks."
        )

    if status != "ready":
        error = video.get("error")
        if isinstance(error, dict):
            code = str(error.get("code", status))
            message = str(error.get("message", "Video generation failed."))
            request_id = error.get("request_id")
            if request_id:
                message = f"{message} Viggle request ID: {request_id}."
            raise RuntimeError(f"Viggle video {status} ({code}): {message}")
        raise RuntimeError(f"Viggle video generation ended with status {status!r}.")

    video_url = video.get("video_url")
    if not isinstance(video_url, str) or not video_url.startswith("https://"):
        raise ValueError("Viggle marked the video ready without a valid HTTPS video URL.")

    video_response = requests.get(video_url, timeout=180)
    video_response.raise_for_status()
    if not video_response.content:
        raise ValueError("Viggle returned an empty video file.")
    return video_response.content


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _json_response(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    if response.status_code >= 400:
        error = payload.get("error", {})
        if isinstance(error, dict):
            code = str(error.get("code", "HTTP_ERROR"))
            message = str(error.get("message", response.reason or "The request was rejected."))
            request_id = error.get("request_id")
            if request_id:
                message = f"{message} Viggle request ID: {request_id}."
        else:
            code = "HTTP_ERROR"
            message = str(error) or response.reason or "The request was rejected."
        raise ViggleAPIError(response.status_code, code, message)

    return payload
