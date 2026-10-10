"""Google Gemini Omni and Veo image-to-video integrations."""

import base64
import time
from typing import Any

import requests


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"
OMNI_MODEL = "gemini-omni-1.1-flash"
VEO_MODEL = "veo-3.1-generate-preview"
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 180


class GoogleVideoAPIError(RuntimeError):
    """Google API failure with provider status and quota diagnostics."""

    def __init__(self, status_code: int, message: str, details: list[str] | None = None):
        self.status_code = status_code
        self.details = details or []
        detail_text = f" Details: {'; '.join(self.details)}" if self.details else ""
        super().__init__(f"Google Gemini API returned HTTP {status_code}: {message}{detail_text}")


def validate_api_key(api_key: str) -> None:
    """Verify that Google accepts the API key without starting video generation."""
    response = requests.get(
        f"{GEMINI_API_URL}/models",
        headers={"x-goog-api-key": api_key},
        timeout=30,
    )
    _raise_for_google_status(response)


def animate_with_omni(image_bytes: bytes, prompt: str, api_key: str) -> bytes:
    """Generate image-conditioned video with Gemini Omni Flash."""
    response = requests.post(
        f"{GEMINI_API_URL}/interactions",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "model": OMNI_MODEL,
            "input": [
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                    "mime_type": "image/png",
                },
                {"type": "text", "text": prompt},
            ],
            "response_format": {"type": "video"},
            "store": False,
        },
        timeout=900,
    )
    _raise_for_google_status(response)
    payload = response.json()
    if payload.get("status") not in (None, "completed"):
        raise RuntimeError(
            f"Gemini Omni did not complete video generation (status: {payload['status']})."
        )
    video_data = _omni_video_data(payload)
    if not video_data:
        raise ValueError("Gemini Omni returned no video data.")
    try:
        return base64.b64decode(video_data, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Gemini Omni returned invalid base64 video data.") from exc


def animate_with_veo(
    image_bytes: bytes,
    prompt: str,
    api_key: str,
    *,
    poll_interval: int = POLL_INTERVAL_SECONDS,
    max_poll_attempts: int = MAX_POLL_ATTEMPTS,
) -> bytes:
    """Generate image-conditioned video with Veo 3.1 and return its MP4 bytes."""
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{GEMINI_API_URL}/models/{VEO_MODEL}:predictLongRunning",
        headers=headers,
        json={
            "instances": [
                {
                    "prompt": prompt,
                    "image": {
                        "bytesBase64Encoded": base64.b64encode(image_bytes).decode("ascii"),
                        "mimeType": "image/png",
                    },
                }
            ]
        },
        timeout=60,
    )
    _raise_for_google_status(response)
    operation = response.json()
    operation_name = operation.get("name")
    if not isinstance(operation_name, str) or not operation_name:
        raise ValueError("Veo did not return a video-generation operation name.")

    for attempt in range(max_poll_attempts):
        if attempt:
            time.sleep(poll_interval)
        operation_response = requests.get(
            f"{GEMINI_API_URL}/{operation_name}",
            headers={"x-goog-api-key": api_key},
            timeout=60,
        )
        _raise_for_google_status(operation_response)
        operation = operation_response.json()
        if operation.get("done"):
            break
    else:
        raise TimeoutError(
            f"Veo video generation did not finish after {max_poll_attempts} checks."
        )

    if operation.get("error"):
        error = operation["error"]
        raise RuntimeError(f"Veo video generation failed: {error.get('message', error)}")

    video_uri = _veo_video_uri(operation)
    if not video_uri:
        raise ValueError("Veo completed without returning a video download URL.")
    video_response = requests.get(
        video_uri,
        headers={"x-goog-api-key": api_key},
        timeout=180,
    )
    _raise_for_google_status(video_response)
    if not video_response.content:
        raise ValueError("Veo returned an empty video file.")
    return video_response.content


def _omni_video_data(payload: dict[str, Any]) -> str | None:
    output_video = payload.get("output_video")
    if isinstance(output_video, dict) and isinstance(output_video.get("data"), str):
        return output_video["data"]

    for step in reversed(payload.get("steps", [])):
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue
        for content in step.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "video"
                and isinstance(content.get("data"), str)
            ):
                return content["data"]
    return None


def _veo_video_uri(operation: dict[str, Any]) -> str | None:
    try:
        uri = operation["response"]["generateVideoResponse"]["generatedSamples"][0]["video"][
            "uri"
        ]
    except (KeyError, IndexError, TypeError):
        return None
    return uri if isinstance(uri, str) else None


def _raise_for_google_status(response: requests.Response) -> None:
    status_code = response.status_code
    if status_code < 400:
        return

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not isinstance(error, dict):
        error = {}
    message = error.get("message")
    if not isinstance(message, str) or not message:
        message = response.reason or "The request was rejected."

    details: list[str] = []
    for item in error.get("details", []):
        if not isinstance(item, dict):
            continue
        for key in ("reason", "retryDelay"):
            value = item.get(key)
            if isinstance(value, str) and value not in details:
                details.append(value)
        metadata = item.get("metadata")
        if isinstance(metadata, dict):
            for key in ("quotaMetric", "quotaId", "quotaLimit", "service"):
                value = metadata.get(key)
                if isinstance(value, str):
                    details.append(f"{key}={value}")

    raise GoogleVideoAPIError(status_code, message, details)
