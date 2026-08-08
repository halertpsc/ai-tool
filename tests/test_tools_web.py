from unittest.mock import MagicMock, patch

from vllm_cli.tools.web import fetch_url


def test_fetch_url_rejects_non_http_scheme(tmp_path):
    result = fetch_url(tmp_path, "ftp://example.com/file")
    assert "Error" in result
    assert "scheme" in result


def test_fetch_url_rejects_schemeless(tmp_path):
    result = fetch_url(tmp_path, "not-a-url")
    assert "Error" in result


def test_fetch_url_success(tmp_path):
    mock_resp = MagicMock(status_code=200, text="page body")
    with patch("vllm_cli.tools.web.httpx.get", return_value=mock_resp) as mock_get:
        result = fetch_url(tmp_path, "https://example.com")
    mock_get.assert_called_once()
    assert "HTTP 200" in result
    assert "page body" in result


def test_fetch_url_truncates_large_body(tmp_path):
    mock_resp = MagicMock(status_code=200, text="x" * 20000)
    with patch("vllm_cli.tools.web.httpx.get", return_value=mock_resp):
        result = fetch_url(tmp_path, "https://example.com")
    assert "truncated" in result
