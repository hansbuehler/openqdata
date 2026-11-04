"""Request-origin checks exercise the real credential-injecting transport offline."""
from types import SimpleNamespace

import pytest
import requests

from quantdata.massive import MassiveClient


@pytest.mark.parametrize("url", [
    "https://external.invalid/quotes", "http://api.massive.com/quotes",
    "https://api.massive.com.external.invalid/quotes", "https://api.massive.com@external.invalid/quotes",
    "https://api.massive.com:444/quotes", "//external.invalid/quotes",
])
def test_external_urls_rejected_before_credentials(monkeypatch, url):
    def blocked():
        raise AssertionError("Credentials must not be read for external URLs")
    monkeypatch.setattr(MassiveClient, "get_token", blocked)
    with pytest.raises(ValueError, match="API origin"):
        MassiveClient().get(url)


@pytest.mark.parametrize("next_url,valid", [
    ("https://external.invalid/page2", False),
    ("/v3/trades/SPY?cursor=next", True),
    ("https://api.massive.com/v3/trades/SPY?cursor=next", True),
])
def test_pagination_keeps_credentials_on_api_origin(monkeypatch, next_url, valid):
    client, calls = MassiveClient(), []
    monkeypatch.setattr(MassiveClient, "get_token", lambda: "test-token")
    def get(url, *, params, timeout, allow_redirects):
        assert params["apiKey"] == "test-token" and not allow_redirects
        calls.append(url)
        data = {"results": [{"id": 1}], "next_url": next_url} if len(calls) == 1 else {"results": [{"id": 2}]}
        return SimpleNamespace(status_code=200, raise_for_status=lambda: None, json=lambda: data)
    client._session = SimpleNamespace(get=get)
    if valid:
        assert client.paginate(client.BASE_URL + "/v3/trades/SPY") == [{"id": 1}, {"id": 2}]
        assert calls[1] == client.BASE_URL + "/v3/trades/SPY?cursor=next"
    else:
        with pytest.raises(ValueError, match="API origin"):
            client.paginate(client.BASE_URL + "/v3/trades/SPY")
        assert len(calls) == 1


def test_redirect_is_not_followed(monkeypatch):
    client, calls = MassiveClient(), []
    monkeypatch.setattr(MassiveClient, "get_token", lambda: "test-token")
    response = requests.Response()
    response.status_code = 302
    response.headers["Location"] = "https://external.invalid/quotes"
    def get(url, **kwargs):
        calls.append(url)
        assert kwargs["allow_redirects"] is False
        return response
    client._session = SimpleNamespace(get=get)
    with pytest.raises(ValueError, match="redirects"):
        client.get(client.BASE_URL + "/v3/trades/SPY")
    assert len(calls) == 1
