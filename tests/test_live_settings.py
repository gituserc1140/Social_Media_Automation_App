from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_shows_provider_key_inputs_without_demo_mode():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()

    assert not app.exception
    assert not any(toggle.label == "Demo mode" for toggle in app.toggle)
    labels = {field.label for field in app.text_input}
    assert {
        "OpenAI API key",
        "Cohere API key",
        "Viggle API key",
        "Buffer API key",
    }.issubset(labels)
    assert "Hugging Face token" not in labels
    assert "Google Gemini API key" not in labels
    assert "fal.ai API key" not in labels
    assert "Cloudinary cloud name" not in labels
    assert "Cloudinary API key" not in labels
    assert "Cloudinary API secret" not in labels
    assert "Animation model" not in {select.label for select in app.selectbox}
    assert not any(button.label == "Generate soundtrack" for button in app.button)
    assert not any("Simulate" in button.label for button in app.button)


def test_image_generation_requires_openai_key():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()

    next(
        field for field in app.text_input
        if field.label == "Describe your pixel-art scene"
    ).set_value("a small robot")
    app.run()
    next(button for button in app.button if button.label == "Generate with OpenAI").click()
    app.run()

    assert not app.exception
    assert app.session_state["pixel_art_image"] is None
    assert any("Enter your OpenAI API key" in item.value for item in app.error)


def test_uploaded_audio_track_remains_available():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()

    uploader = next(
        uploader for uploader in app.file_uploader
        if uploader.label == "Upload an audio track"
    )
    uploader.upload("soundtrack.wav", b"audio-track-bytes", "audio/wav")
    app.run()

    assert not app.exception
    assert app.session_state["music_bytes"] == b"audio-track-bytes"
    assert app.session_state["music_extension"] == "wav"
    assert any(button.label == "Download soundtrack" for button in app.download_button)
