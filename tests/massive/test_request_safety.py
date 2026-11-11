"""Request-origin checks exercise the real credential-injecting transport offline."""
from types import SimpleNamespace

import pytest
import requests

from oqdata.massive import MassiveClient


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
    def get(url, *, params, headers, timeout, allow_redirects):
        assert headers == {"Authorization": "Bearer test-token"} and not allow_redirects
        assert "apiKey" not in (params or {}) and "test-token" not in url
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


def _response(status):
    response = requests.Response()
    response.status_code = status
    response.url = MassiveClient.BASE_URL + "/v3/trades/SPY"
    return response


@pytest.mark.parametrize("status", [400, 401, 404, 501, 505])
def test_non_transient_http_errors_raise_immediately(monkeypatch, status):
    client, calls = MassiveClient(), []
    monkeypatch.setattr(MassiveClient, "get_token", lambda: "test-token")
    monkeypatch.setattr("oqdata.massive.client.pytime.sleep", lambda s: pytest.fail("must not retry"))
    def get(url, **kwargs):
        calls.append(url)
        return _response(status)
    client._session = SimpleNamespace(get=get)
    with pytest.raises(requests.exceptions.HTTPError) as err:
        client.get(client.BASE_URL + "/v3/trades/SPY")
    assert len(calls) == 1
    assert "test-token" not in str(err.value)


@pytest.mark.parametrize("failure", ["status", "timeout"])
def test_transient_failures_retry_with_cap_and_growing_timeout(monkeypatch, failure):
    client, timeouts, sleeps = MassiveClient(), [], []
    monkeypatch.setattr(MassiveClient, "get_token", lambda: "test-token")
    monkeypatch.setattr("oqdata.massive.client.pytime.sleep", sleeps.append)
    def get(url, *, timeout, **kwargs):
        timeouts.append(timeout)
        if failure == "timeout":
            raise requests.exceptions.ReadTimeout("read timed out")
        return _response(503)
    client._session = SimpleNamespace(get=get)
    with pytest.warns(UserWarning, match="Massive error"):
        with pytest.raises((requests.exceptions.HTTPError, requests.exceptions.ReadTimeout)):
            client.get(client.BASE_URL + "/v3/trades/SPY")
    assert len(timeouts) == MassiveClient.MAX_RETRIES + 1
    assert timeouts == sorted(timeouts) and timeouts[-1] > timeouts[0]
    assert sleeps == list(range(1, MassiveClient.MAX_RETRIES + 1))


def test_transient_failure_then_success(monkeypatch):
    client, calls = MassiveClient(), []
    monkeypatch.setattr(MassiveClient, "get_token", lambda: "test-token")
    monkeypatch.setattr("oqdata.massive.client.pytime.sleep", lambda s: None)
    def get(url, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            return _response(502)
        return SimpleNamespace(status_code=200, raise_for_status=lambda: None, json=lambda: {"ok": True})
    client._session = SimpleNamespace(get=get)
    with pytest.warns(UserWarning, match="retry 1/"):
        assert client.get(client.BASE_URL + "/v3/trades/SPY") == {"ok": True}
    assert len(calls) == 2
