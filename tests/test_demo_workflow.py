from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_key_free_demo_workflow():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    assert not app.exception
    next(toggle for toggle in app.toggle if toggle.label == "Demo mode").set_value(True)
    app.run()

    next(field for field in app.text_input if field.label == "Describe your pixel-art scene").set_value(
        "a tiny robot under a starry sky"
    )
    app.run()

    next(button for button in app.button if button.label == "Generate with OpenAI").click()
    app.run()
    assert app.session_state["pixel_art_image"]

    next(button for button in app.button if button.label == "Create animation").click()
    app.run()
    assert app.session_state["animation_type"] == "gif"

    next(button for button in app.button if button.label == "Generate caption and hashtags").click()
    app.run()
    assert "#PixelArt" in app.session_state["caption_text"]

    next(button for button in app.button if button.label == "Simulate adding post to Buffer").click()
    app.run()
    assert not app.exception
    assert any("Nothing was published" in item.value for item in app.success)
