"""OpenAI image and caption helpers."""

import base64

import requests


OPENAI_API_URL = "https://api.openai.com/v1"


def validate_api_key(api_key: str) -> None:
    """Check that OpenAI accepts the key without making a billable request."""
    response = requests.get(
        f"{OPENAI_API_URL}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()


def generate_pixel_art(prompt: str, api_key: str) -> bytes:
    response = requests.post(
        f"{OPENAI_API_URL}/images/generations",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-image-1",
            "prompt": f"Create crisp, charming pixel art: {prompt}. "
            "Use a limited retro game palette, visible square pixels, and no text.",
            "size": "1024x1024",
        },
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        return base64.b64decode(payload["data"][0]["b64_json"], validate=True)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError("OpenAI returned an image response without valid image data.") from exc


def generate_caption(prompt: str, api_key: str) -> str:
    response = requests.post(
        f"{OPENAI_API_URL}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write one short, engaging social media caption for this pixel-art "
                        f"creation: {prompt!r}. Add 3 to 5 relevant hashtags. Return only "
                        "the caption and hashtags."
                    ),
                }
            ],
            "max_tokens": 160,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        caption = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("OpenAI returned a response without caption text.") from exc
    if not isinstance(caption, str) or not caption.strip():
        raise ValueError("OpenAI returned an empty caption.")
    return caption.strip()
