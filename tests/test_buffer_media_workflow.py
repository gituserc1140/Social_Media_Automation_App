from pathlib import Path

from streamlit.testing.v1 import AppTest

import buffer_client
import cloudinary_service
from pixel_art import create_demo_pixel_art


def test_generated_animation_is_hosted_and_attached_to_buffer_post(monkeypatch):
    uploaded = {}
    published = {}

    def fake_upload(media_bytes, **kwargs):
        uploaded.update(media_bytes=media_bytes, **kwargs)
        return "https://res.cloudinary.com/demo/video/upload/animation.mp4"

    def fake_create_post(**kwargs):
        published.update(kwargs)
        return {"id": "post-1"}

    monkeypatch.setattr(cloudinary_service, "upload_media", fake_upload)
    monkeypatch.setattr(buffer_client, "create_post", fake_create_post)

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    assert not app.exception

    app.session_state["pixel_art_image"] = create_demo_pixel_art("test art")
    app.session_state["animation_bytes"] = b"generated-video-bytes"
    app.session_state["animation_type"] = "mp4"
    app.session_state["caption_text"] = "A tiny pixel-world adventure #PixelArt"
    app.session_state["buffer_organizations"] = [{"id": "org-1", "name": "Studio"}]
    app.session_state["buffer_channels"] = [
        {"id": "channel-1", "name": "studio", "service": "tiktok"}
    ]
    app.session_state["buffer_api_key"] = "buffer-key"
    app.session_state["cloudinary_cloud_name"] = "demo"
    app.session_state["cloudinary_api_key"] = "cloudinary-key"
    app.session_state["cloudinary_api_secret"] = "cloudinary-secret"
    app.run()
    assert not app.exception

    next(button for button in app.button if button.label == "Add post to queue").click()
    app.run()

    assert not app.exception
    assert uploaded["media_bytes"] == b"generated-video-bytes"
    assert uploaded["resource_type"] == "video"
    assert uploaded["mime_type"] == "video/mp4"
    assert published["media_url"] == "https://res.cloudinary.com/demo/video/upload/animation.mp4"
    assert published["media_kind"] == "video"
    assert published["channel_id"] == "channel-1"
