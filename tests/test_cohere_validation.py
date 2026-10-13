import cohere_service


class FakeResponse:
    def __init__(self):
        self.status_checked = False

    def raise_for_status(self):
        self.status_checked = True


def test_validate_api_key_checks_models_endpoint_without_generation(monkeypatch):
    request = {}
    response = FakeResponse()

    def fake_get(url, **kwargs):
        request.update(url=url, **kwargs)
        return response

    monkeypatch.setattr(cohere_service.requests, "get", fake_get)
    monkeypatch.setattr(
        cohere_service.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Credential validation must not generate a completion.")
        ),
    )

    cohere_service.validate_api_key("cohere-session-key")

    assert request["url"] == "https://api.cohere.com/v1/models"
    assert request["headers"]["Authorization"] == "******"
    assert response.status_checked
