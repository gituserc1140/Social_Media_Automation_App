from io import BytesIO
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest

import cohere_service
import openai_service


def test_live_image_generation_uses_server_openai_key(monkeypatch):
    calls = {}
    image = BytesIO()
    Image.new("RGB", (8, 8), (40, 80, 120)).save(image, format="PNG")

    def fake_generate_pixel_art(prompt, api_key):
        calls.update(prompt=prompt, api_key=api_key)
        return image.getvalue()

    monkeypatch.setattr(openai_service, "generate_pixel_art", fake_generate_pixel_art)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-server-key")
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py")
    app.session_state["image_prompt"] = "a small robot"
    app.run()

    next(button for button in app.button if button.label == "Generate with OpenAI").click()
    app.run()

    assert not app.exception
    assert calls == {"prompt": "a small robot", "api_key": "openai-server-key"}
    assert app.session_state["pixel_art_image"] == image.getvalue()


def test_live_caption_generation_uses_cohere(monkeypatch):
    calls = {}

    def fake_generate_caption(prompt, api_key):
        calls.update(prompt=prompt, api_key=api_key)
        return "A little pixel magic #PixelArt"

    image = BytesIO()
    Image.new("RGB", (8, 8), (40, 80, 120)).save(image, format="PNG")

    monkeypatch.setattr(cohere_service, "generate_caption", fake_generate_caption)
    monkeypatch.setenv("COHERE_API_KEY", "cohere-session-key")
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py")
    app.session_state["pixel_art_image"] = image.getvalue()
    app.run()

    next(button for button in app.button if button.label == "Generate caption and hashtags").click()
    app.run()

    assert not app.exception
    assert calls == {"prompt": "A pixel-art creation", "api_key": "cohere-session-key"}
    assert app.session_state["caption_text"] == "A little pixel magic #PixelArt"
