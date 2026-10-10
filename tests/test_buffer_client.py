import buffer_client


def test_identifies_social_profile_and_share_page_urls():
    assert buffer_client.is_social_media_page_url("https://www.tiktok.com/@studio")
    assert buffer_client.is_social_media_page_url("https://www.youtube.com/watch?v=abc")
    assert buffer_client.is_social_media_page_url("https://www.instagram.com/reel/abc/")


def test_does_not_reject_direct_media_host_url():
    assert not buffer_client.is_social_media_page_url(
        "https://cdn.example.test/media/animation.mp4"
    )


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_get_channels_uses_organization_id_variable(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse({"data": {"channels": [{"id": "c1", "name": "Art", "service": "x"}]}})

    monkeypatch.setattr(buffer_client.requests, "post", fake_post)

    channels = buffer_client.get_channels("org-1", "session-token")

    assert channels[0]["id"] == "c1"
    assert captured["headers"]["Authorization"] == "Bearer session-token"
    assert captured["json"]["variables"] == {"organizationId": "org-1"}


def test_create_post_escapes_text_and_includes_schedule_and_media(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse({"data": {"createPost": {"post": {"id": "p1"}}}})

    monkeypatch.setattr(buffer_client.requests, "post", fake_post)

    post = buffer_client.create_post(
        channel_id="channel-1",
        text='Pixel art says "hello"',
        api_key="session-token",
        mode="customScheduled",
        due_at="2026-10-11T12:30:00Z",
        media_url="https://cdn.example.test/art.png",
        media_kind="image",
    )

    query = captured["json"]["query"]
    assert post["id"] == "p1"
    assert 'text: "Pixel art says \\"hello\\""' in query
    assert "mode: customScheduled" in query
    assert 'dueAt: "2026-10-11T12:30:00Z"' in query
    assert "image: { url:" in query


def test_create_post_rejects_custom_schedule_without_time():
    try:
        buffer_client.create_post(
            channel_id="channel-1",
            text="Caption",
            api_key="session-token",
            mode="customScheduled",
        )
    except ValueError as exc:
        assert "requires a date and time" in str(exc)
    else:
        raise AssertionError("Expected missing schedule time to fail.")
