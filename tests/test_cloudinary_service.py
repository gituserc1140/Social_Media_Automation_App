from hashlib import sha1

import cloudinary_service


class FakeResponse:
    status_code = 200
    reason = "OK"

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def test_upload_media_signs_and_uploads_video(monkeypatch):
    request = {}

    def fake_post(url, **kwargs):
        request.update(url=url, **kwargs)
        return FakeResponse({"secure_url": "https://res.cloudinary.com/demo/video/upload/clip.mp4"})

    monkeypatch.setattr(cloudinary_service.requests, "post", fake_post)
    monkeypatch.setattr(cloudinary_service, "time", lambda: 12345)

    url = cloudinary_service.upload_media(
        b"video-bytes",
        cloud_name="demo",
        api_key="api-key",
        api_secret="api-secret",
        resource_type="video",
        filename="animation.mp4",
        mime_type="video/mp4",
    )

    assert url == "https://res.cloudinary.com/demo/video/upload/clip.mp4"
    assert request["url"] == "https://api.cloudinary.com/v1_1/demo/video/upload"
    assert request["data"]["timestamp"] == 12345
    assert request["data"]["folder"] == "pixel-post-studio"
    assert request["data"]["api_key"] == "api-key"
    assert request["data"]["signature"] == sha1(
        b"folder=pixel-post-studio&timestamp=12345api-secret"
    ).hexdigest()
    assert request["files"]["file"] == ("animation.mp4", b"video-bytes", "video/mp4")


def test_upload_rejects_empty_media_before_request(monkeypatch):
    monkeypatch.setattr(
        cloudinary_service.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Empty media must not be sent.")
        ),
    )

    try:
        cloudinary_service.upload_media(
            b"",
            cloud_name="demo",
            api_key="api-key",
            api_secret="api-secret",
            resource_type="video",
            filename="animation.mp4",
            mime_type="video/mp4",
        )
    except ValueError as exc:
        assert "empty media" in str(exc)
    else:
        raise AssertionError("Expected empty media to be rejected.")
