from pathlib import Path

from streamlit.testing.v1 import AppTest

import buffer_client
import media_service


def test_uploaded_animation_can_be_converted_and_published_without_pixel_art(monkeypatch):
    published = {}

    def fake_convert(video_bytes, zoom):
        assert video_bytes == b"uploaded-video-bytes"
        assert zoom == 1.2
        return b"converted-video-bytes"

    def fake_create_post(**kwargs):
        published.update(kwargs)
        return {"id": "post-uploaded"}

    monkeypatch.setattr(media_service, "convert_to_tiktok_format", fake_convert)
    monkeypatch.setattr(buffer_client, "create_post", fake_create_post)

    monkeypatch.setenv("BUFFER_API_KEY", "buffer-key")
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py")
    app.session_state["buffer_organizations"] = [{"id": "org-1", "name": "Studio"}]
    app.session_state["buffer_channels"] = [
        {"id": "channel-1", "name": "studio", "service": "instagram"}
    ]
    app.session_state["caption_text"] = "An uploaded animation"
    app.run()
    app.file_uploader[1].upload(
        "existing-animation.mp4",
        b"uploaded-video-bytes",
        "video/mp4",
    )
    app.run()

    assert not app.exception
    assert app.session_state["animation_bytes"] == b"uploaded-video-bytes"
    assert app.session_state["animation_type"] == "mp4"
    assert any(
        "Create pixel art to generate an animation" in item.value
        for item in app.info
    )
    assert not any(
        "Create pixel art before writing a caption" in item.value
        for item in app.info
    )

    next(slider for slider in app.slider if slider.label == "Video zoom").set_value(1.2)
    app.run()
    next(
        button
        for button in app.button
        if button.label == "Convert video to 1080 × 1920"
    ).click()
    app.run()
    assert not app.exception
    assert app.session_state["animation_bytes"] == b"uploaded-video-bytes"
    assert (
        app.session_state["converted_animation_bytes"] == b"converted-video-bytes"
    )
    assert any(
        button.label == "Download converted TikTok video (1080 × 1920)"
        for button in app.download_button
    )

    assert not any(button.label == "Upload video to Cloudinary" for button in app.button)
    next(radio for radio in app.radio if radio.label == "Post media").set_value(
        "Use a public media URL"
    )
    app.run()
    next(
        field
        for field in app.text_input
        if field.label == "Direct public image/video file URL"
    ).set_value("https://media.example.com/tiktok-video.mp4")
    app.run()

    next(button for button in app.button if button.label == "Add post to queue").click()
    app.run()

    assert not app.exception
    assert published["media_url"] == "https://media.example.com/tiktok-video.mp4"
    assert published["media_kind"] == "video"
    assert published["channel_id"] == "channel-1"
