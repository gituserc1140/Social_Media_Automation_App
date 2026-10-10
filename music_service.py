"""Hugging Face music generation integration."""

import requests


MUSIC_MODEL = "facebook/musicgen-small"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{MUSIC_MODEL}"


def validate_api_key(api_key: str) -> None:
    """Check that Hugging Face accepts the token without generating audio."""
    response = requests.get(
        "https://huggingface.co/api/whoami-v2",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()


def generate_music(prompt: str, api_key: str) -> tuple[bytes, str]:
    response = requests.post(
        HF_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={"inputs": prompt},
        timeout=300,
    )
    if not response.ok:
        detail = response.text[:500].strip()
        raise RuntimeError(
            f"Hugging Face music generation failed (HTTP {response.status_code}): "
            f"{detail or 'no details returned'}"
        )
    content_type = response.headers.get("Content-Type", "").split(";", maxsplit=1)[0]
    if not response.content or not content_type.startswith("audio/"):
        raise ValueError(
            "Hugging Face did not return audio. Check model availability and your API access."
        )
    extension = "wav" if content_type == "audio/wav" else "mp3"
    return response.content, extension
