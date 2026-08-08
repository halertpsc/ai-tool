from vllm_cli.client import VllmClient


def test_headers_include_referer_and_title_when_set():
    client = VllmClient("http://localhost:8000", "model", referer="https://example.com", title="My App")
    try:
        assert client._client.headers["HTTP-Referer"] == "https://example.com"
        assert client._client.headers["X-Title"] == "My App"
    finally:
        client.close()


def test_headers_omit_referer_and_title_when_unset():
    client = VllmClient("http://localhost:8000", "model")
    try:
        assert "HTTP-Referer" not in client._client.headers
        assert "X-Title" not in client._client.headers
    finally:
        client.close()


def test_headers_include_api_key_and_referer_together():
    client = VllmClient("http://localhost:8000", "model", api_key="secret", referer="https://example.com")
    try:
        assert client._client.headers["Authorization"] == "Bearer secret"
        assert client._client.headers["HTTP-Referer"] == "https://example.com"
        assert "X-Title" not in client._client.headers
    finally:
        client.close()
