from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_live_mode_is_default_and_shows_provider_key_inputs():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()

    assert not app.exception
    assert next(toggle for toggle in app.toggle if toggle.label == "Demo mode").value is False
    labels = {field.label for field in app.text_input}
    assert {
        "OpenAI API key",
        "Google Gemini API key",
        "fal.ai API key",
        "Viggle API key",
        "Cloudinary cloud name",
        "Cloudinary API key",
        "Cloudinary API secret",
        "Hugging Face token",
        "Buffer API key",
    }.issubset(labels)
