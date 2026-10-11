import cohere_service
import music_service
import openai_service


class FakeResponse:
    def __init__(self, payload=None):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_cohere_caption_request_returns_generated_text(monkeypatch):
    request = {}
    response = FakeResponse(
        {"message": {"content": [{"type": "text", "text": "Pixel magic! #PixelArt"}]}}
    )

    def fake_post(url, **kwargs):
        request.update(url=url, **kwargs)
        return response

    monkeypatch.setattr(cohere_service.requests, "post", fake_post)

    caption = cohere_service.generate_caption("a pixel-art garden", "cohere-session-key")

    assert caption == "Pixel magic! #PixelArt"
    assert request["url"] == "https://api.cohere.com/v2/chat"
    assert request["headers"]["Authorization"] == "Bearer cohere-session-key"
    assert request["json"]["model"] == "command-r-08-2024"


def test_cohere_caption_rejects_missing_text(monkeypatch):
    monkeypatch.setattr(
        cohere_service.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"message": {"content": []}}),
    )

    try:
        cohere_service.generate_caption("pixel art", "cohere-session-key")
    except ValueError as exc:
        assert "without caption text" in str(exc)
    else:
        raise AssertionError("Expected missing Cohere caption text to raise ValueError.")

def test_openai_key_check_uses_non_billable_models_endpoint(monkeypatch):
    request = {}

    def fake_get(url, **kwargs):
        request.update(url=url, **kwargs)
        return FakeResponse()

    monkeypatch.setattr(openai_service.requests, "get", fake_get)

    openai_service.validate_api_key("openai-session-key")

    assert request["url"] == "https://api.openai.com/v1/models"
    assert request["headers"]["Authorization"] == "Bearer openai-session-key"


def test_hugging_face_token_check_uses_whoami_endpoint(monkeypatch):
    request = {}

    def fake_get(url, **kwargs):
        request.update(url=url, **kwargs)
        return FakeResponse()

    monkeypatch.setattr(music_service.requests, "get", fake_get)

    music_service.validate_api_key("hf-session-token")

    assert request["url"] == "https://huggingface.co/api/whoami-v2"
    assert request["headers"]["Authorization"] == "Bearer hf-session-token"
