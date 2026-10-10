import base64

import google_video_service


class FakeResponse:
    def __init__(self, payload=None, content=b"", status_code=200):
        self.payload = payload or {}
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_omni_sends_image_and_extracts_video_without_storing_interaction(monkeypatch):
    captured = {}
    video_bytes = b"generated-mp4"

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return FakeResponse(
            {
                "status": "completed",
                "steps": [
                    {
                        "type": "model_output",
                        "content": [
                            {
                                "type": "video",
                                "mime_type": "video/mp4",
                                "data": base64.b64encode(video_bytes).decode("ascii"),
                            }
                        ],
                    }
                ],
            }
        )

    monkeypatch.setattr(google_video_service.requests, "post", fake_post)

    result = google_video_service.animate_with_omni(b"pixel-png", "Animate gently", "gemini-key")

    assert result == video_bytes
    assert captured["url"].endswith("/interactions")
    assert captured["headers"]["x-goog-api-key"] == "gemini-key"
    assert captured["json"]["model"] == "gemini-omni-1.1-flash"
    assert captured["json"]["input"][0]["data"] == base64.b64encode(b"pixel-png").decode(
        "ascii"
    )
    assert captured["json"]["store"] is False


def test_veo_polls_operation_and_downloads_video(monkeypatch):
    post_request = {}
    get_requests = []
    video_bytes = b"veo-mp4"

    def fake_post(url, **kwargs):
        post_request.update(url=url, **kwargs)
        return FakeResponse({"name": "operations/video-1"})

    def fake_get(url, **kwargs):
        get_requests.append((url, kwargs))
        if url.endswith("operations/video-1"):
            return FakeResponse(
                {
                    "done": True,
                    "response": {
                        "generateVideoResponse": {
                            "generatedSamples": [{"video": {"uri": "https://media.example/video"}}]
                        }
                    },
                }
            )
        return FakeResponse(content=video_bytes)

    monkeypatch.setattr(google_video_service.requests, "post", fake_post)
    monkeypatch.setattr(google_video_service.requests, "get", fake_get)
    monkeypatch.setattr(google_video_service.time, "sleep", lambda _: None)

    result = google_video_service.animate_with_veo(
        b"pixel-png",
        "Animate gently",
        "gemini-key",
        poll_interval=0,
        max_poll_attempts=1,
    )

    assert result == video_bytes
    assert post_request["url"].endswith(
        "/models/veo-3.1-generate-preview:predictLongRunning"
    )
    assert post_request["json"]["instances"][0]["image"]["bytesBase64Encoded"] == (
        base64.b64encode(b"pixel-png").decode("ascii")
    )
    assert get_requests[-1][0] == "https://media.example/video"
    assert get_requests[-1][1]["headers"]["x-goog-api-key"] == "gemini-key"


def test_omni_rejects_missing_video_output(monkeypatch):
    monkeypatch.setattr(
        google_video_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"status": "completed", "steps": []}),
    )

    try:
        google_video_service.animate_with_omni(b"pixel-png", "Animate gently", "gemini-key")
    except ValueError as exc:
        assert "no video data" in str(exc)
    else:
        raise AssertionError("Expected missing video output to fail.")


def test_omni_reports_google_quota_reason_for_429(monkeypatch):
    monkeypatch.setattr(
        google_video_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            {
                "error": {
                    "code": 429,
                    "message": "Quota exceeded for this model.",
                    "status": "RESOURCE_EXHAUSTED",
                    "details": [
                        {
                            "reason": "RATE_LIMIT_EXCEEDED",
                            "metadata": {
                                "quotaMetric": "generativelanguage.googleapis.com/requests"
                            },
                        }
                    ],
                }
            },
            status_code=429,
        ),
    )

    try:
        google_video_service.animate_with_omni(b"pixel-png", "Animate gently", "gemini-key")
    except google_video_service.GoogleVideoAPIError as exc:
        assert exc.status_code == 429
        assert "Quota exceeded for this model" in str(exc)
        assert "RATE_LIMIT_EXCEEDED" in str(exc)
        assert "quotaMetric=generativelanguage.googleapis.com/requests" in str(exc)
    else:
        raise AssertionError("Expected Google quota errors to retain provider details.")


def test_veo_reports_quota_error_when_polling_operation(monkeypatch):
    monkeypatch.setattr(
        google_video_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"name": "operations/video-1"}),
    )
    monkeypatch.setattr(
        google_video_service.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {"error": {"message": "Quota exceeded."}},
            status_code=429,
        ),
    )

    try:
        google_video_service.animate_with_veo(
            b"pixel-png",
            "Animate gently",
            "gemini-key",
            poll_interval=0,
            max_poll_attempts=1,
        )
    except google_video_service.GoogleVideoAPIError as exc:
        assert exc.status_code == 429
        assert "Quota exceeded." in str(exc)
    else:
        raise AssertionError("Expected Veo polling quota errors to be reported.")
