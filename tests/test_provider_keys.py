import music_service
import openai_service


class FakeResponse:
    def raise_for_status(self):
        return None


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
