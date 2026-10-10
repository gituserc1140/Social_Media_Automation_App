"""Signed Cloudinary uploads for media attachments sent to Buffer."""

from hashlib import sha1
from time import time
from typing import Any

import requests


CLOUDINARY_API_URL = "https://api.cloudinary.com/v1_1"


def upload_media(
    media_bytes: bytes,
    *,
    cloud_name: str,
    api_key: str,
    api_secret: str,
    resource_type: str,
    filename: str,
    mime_type: str,
    folder: str = "pixel-post-studio",
) -> str:
    """Upload generated media as a public Cloudinary asset and return its URL."""
    if resource_type not in {"image", "video"}:
        raise ValueError("Cloudinary media must be an image or video.")
    if not media_bytes:
        raise ValueError("Cannot upload empty media.")
    if not cloud_name.strip() or not api_key.strip() or not api_secret:
        raise ValueError("Enter your Cloudinary cloud name, API key, and API secret.")

    timestamp = int(time())
    signed_params = {"folder": folder, "timestamp": timestamp}
    signature_base = "&".join(
        f"{key}={signed_params[key]}" for key in sorted(signed_params)
    )
    signature = sha1(f"{signature_base}{api_secret}".encode("utf-8")).hexdigest()
    response = requests.post(
        f"{CLOUDINARY_API_URL}/{cloud_name.strip()}/{resource_type}/upload",
        data={
            **signed_params,
            "api_key": api_key,
            "signature": signature,
        },
        files={"file": (filename, media_bytes, mime_type)},
        timeout=180,
    )
    try:
        payload: dict[str, Any] = response.json()
    except ValueError:
        payload = {}
    if response.status_code >= 400:
        error = payload.get("error", {})
        message = error.get("message") if isinstance(error, dict) else None
        raise RuntimeError(
            f"Cloudinary upload failed (HTTP {response.status_code}): "
            f"{message or response.reason or 'no details returned'}"
        )

    secure_url = payload.get("secure_url")
    if not isinstance(secure_url, str) or not secure_url.startswith("https://"):
        raise ValueError("Cloudinary upload succeeded without returning a public HTTPS URL.")
    return secure_url
