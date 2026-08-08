from typing import Any, Dict, Generator, List, Optional

import httpx

from vllm_cli.sse import StreamInterrupted, parse_sse_stream


class VllmClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str] = None,
        referer: Optional[str] = None,
        title: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        self._client = httpx.Client(headers=headers, timeout=timeout)

    # ------------------------------------------------------------------
    # Payload builders
    # ------------------------------------------------------------------

    def _completion_payload(self, prompt: str, **params: Any) -> dict:
        payload: dict = {"model": self.model, "prompt": prompt}
        for key in ("max_tokens", "temperature", "top_p", "stop"):
            if key in params and params[key] is not None:
                payload[key] = params[key]
        return payload

    def _chat_payload(self, messages: List[dict], **params: Any) -> dict:
        payload: dict = {"model": self.model, "messages": messages}
        for key in ("max_tokens", "temperature", "top_p"):
            if key in params and params[key] is not None:
                payload[key] = params[key]
        return payload

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _raise_for_status(self, resp: httpx.Response) -> None:
        try:
            body = resp.json()
            detail = body.get("error", {}).get("message") or resp.text
        except Exception:
            detail = resp.text
        raise SystemExit(f"API error {resp.status_code}: {detail}")

    # ------------------------------------------------------------------
    # Non-streaming
    # ------------------------------------------------------------------

    def complete(self, prompt: str, **params: Any) -> dict:
        try:
            resp = self._client.post(
                f"{self.base_url}/v1/completions",
                json=self._completion_payload(prompt, **params),
            )
        except httpx.ConnectError:
            raise SystemExit(f"Connection error: could not reach {self.base_url}")
        except httpx.TimeoutException:
            raise SystemExit(f"Timeout: no response from {self.base_url}")
        if not resp.is_success:
            self._raise_for_status(resp)
        return resp.json()

    def chat(self, messages: List[dict], **params: Any) -> dict:
        try:
            resp = self._client.post(
                f"{self.base_url}/v1/chat/completions",
                json=self._chat_payload(messages, **params),
            )
        except httpx.ConnectError:
            raise SystemExit(f"Connection error: could not reach {self.base_url}")
        except httpx.TimeoutException:
            raise SystemExit(f"Timeout: no response from {self.base_url}")
        if not resp.is_success:
            self._raise_for_status(resp)
        return resp.json()

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def complete_stream(self, prompt: str, **params: Any) -> Generator[str, None, None]:
        payload = self._completion_payload(prompt, **params)
        payload["stream"] = True
        try:
            with self._client.stream(
                "POST", f"{self.base_url}/v1/completions", json=payload
            ) as resp:
                if not resp.is_success:
                    resp.read()
                    self._raise_for_status(resp)
                try:
                    yield from parse_sse_stream(resp.iter_lines())
                except Exception as exc:
                    raise StreamInterrupted(str(exc)) from exc
        except httpx.ConnectError:
            raise SystemExit(f"Connection error: could not reach {self.base_url}")

    def chat_stream(self, messages: List[dict], **params: Any) -> Generator[str, None, None]:
        payload = self._chat_payload(messages, **params)
        payload["stream"] = True
        try:
            with self._client.stream(
                "POST", f"{self.base_url}/v1/chat/completions", json=payload
            ) as resp:
                if not resp.is_success:
                    resp.read()
                    self._raise_for_status(resp)
                try:
                    yield from parse_sse_stream(resp.iter_lines())
                except Exception as exc:
                    raise StreamInterrupted(str(exc)) from exc
        except httpx.ConnectError:
            raise SystemExit(f"Connection error: could not reach {self.base_url}")

    def close(self) -> None:
        self._client.close()
