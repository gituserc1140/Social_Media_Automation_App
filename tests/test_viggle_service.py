import viggle_service


class FakeResponse:
    def __init__(self, payload=None, content=b"", status_code=200, reason=""):
        self.payload = payload or {}
        self.content = content
        self.status_code = status_code
        self.reason = reason

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def test_get_credit_balance_authenticates_and_returns_balance(monkeypatch):
    request = {}

    def fake_get(url, **kwargs):
        request.update(url=url, **kwargs)
        return FakeResponse({"balance": 100.0})

    monkeypatch.setattr(viggle_service.requests, "get", fake_get)

    assert viggle_service.get_credit_balance("viggle-session-key") == 100.0
    assert request["url"] == "https://apis.viggle.ai/v1/credits"
    assert request["headers"]["Authorization"] == "Bearer viggle-session-key"


def test_animate_uploads_image_polls_job_and_downloads_video(monkeypatch):
    requests = []
    video_bytes = b"viggle-mp4"

    def fake_post(url, **kwargs):
        requests.append(("POST", url, kwargs))
        return FakeResponse({"id": "vid_123", "status": "queued"})

    def fake_get(url, **kwargs):
        requests.append(("GET", url, kwargs))
        if url.endswith("/videos/vid_123"):
            return FakeResponse({"id": "vid_123", "status": "ready", "video_url": "https://cdn.viggle.ai/video.mp4"})
        return FakeResponse(content=video_bytes)

    monkeypatch.setattr(viggle_service.requests, "post", fake_post)
    monkeypatch.setattr(viggle_service.requests, "get", fake_get)
    monkeypatch.setattr(viggle_service.time, "sleep", lambda _: None)

    result = viggle_service.animate_image(
        b"pixel-png",
        "A gentle idle animation",
        "viggle-session-key",
        quality="high",
        duration_seconds=7,
        poll_interval=0,
        max_poll_attempts=1,
    )

    method, url, request = requests[0]
    assert result == video_bytes
    assert method == "POST"
    assert url == "https://apis.viggle.ai/v1/videos"
    assert request["headers"]["Authorization"] == "Bearer viggle-session-key"
    assert request["data"] == {
        "prompt": "A gentle idle animation",
        "quality": "high",
        "duration_s": "7",
    }
    assert request["files"]["reference_image"] == (
        "pixel-art.png",
        b"pixel-png",
        "image/png",
    )
    assert requests[1][1] == "https://apis.viggle.ai/v1/videos/vid_123"
    assert requests[2][1] == "https://cdn.viggle.ai/video.mp4"


def test_viggle_api_error_includes_remediation_code(monkeypatch):
    monkeypatch.setattr(
        viggle_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            {
                "error": {
                    "code": "INSUFFICIENT_CREDITS",
                    "message": "Add credits to start this job.",
                    "request_id": "req_123",
                }
            },
            status_code=402,
        ),
    )

    try:
        viggle_service.animate_image(b"pixel-png", "Animate", "viggle-key")
    except viggle_service.ViggleAPIError as exc:
        assert exc.status_code == 402
        assert exc.code == "INSUFFICIENT_CREDITS"
        assert "req_123" in str(exc)
    else:
        raise AssertionError("Expected Viggle API errors to surface.")


def test_viggle_rejects_invalid_duration_before_request(monkeypatch):
    def unexpected_request(*args, **kwargs):
        raise AssertionError("No request should be made for invalid duration.")

    monkeypatch.setattr(viggle_service.requests, "post", unexpected_request)

    try:
        viggle_service.animate_image(
            b"pixel-png",
            "Animate",
            "viggle-key",
            duration_seconds=20,
        )
    except ValueError as exc:
        assert "between 3 and 15" in str(exc)
    else:
        raise AssertionError("Expected invalid duration to fail.")
