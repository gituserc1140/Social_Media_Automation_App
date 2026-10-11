"""Cohere caption generation."""

import requests


COHERE_API_URL = "https://api.cohere.com/v2/chat"


def generate_caption(prompt: str, api_key: str) -> str:
    response = requests.post(
        COHERE_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "command-r-08-2024",
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
        content = payload["message"]["content"]
        caption = next(
            item["text"]
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        )
    except (KeyError, IndexError, StopIteration, TypeError) as exc:
        raise ValueError("Cohere returned a response without caption text.") from exc
    if not caption.strip():
        raise ValueError("Cohere returned an empty caption.")
    return caption.strip()
