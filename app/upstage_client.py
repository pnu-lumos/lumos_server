from __future__ import annotations
import json
import asyncio
from dataclasses import dataclass
from typing import Any
import httpx
from .config import Settings
from .prompts import SYSTEM_PROMPT, build_user_prompt

class UpstageClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

@dataclass(frozen = True)
class ParsedDocument:
    markdown: str

class UpstageClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._http = httpx.AsyncClient(
            timeout = settings.request_timeout_sec,
            follow_redirects = True,
            headers = {"Authorization": f"Bearer {settings.upstage_api_key}"},
        )

    async def close(self) -> None:
        await self._http.aclose()
    
    async def parse_document(self, *, image_bytes: bytes, filename: str, content_type: str) -> ParsedDocument:
        payload = await self._parse_with_fallback(image_bytes = image_bytes, filename = filename, content_type = content_type)
        markdown = self._extract_parse_text(payload).strip()
        if not markdown:
            return ParsedDocument(markdown = "NO_TEXT")
        return ParsedDocument(markdown = markdown)

    async def generate_alt_text(self, *, parsed_markdown: str, page_url: str | None) -> str:
        user_prompt = build_user_prompt(parsed_markdown = parsed_markdown, page_url = page_url)
        primary_error: UpstageClientError | None = None
        models = [self._settings.upstage_model, "solar-1-mini-chat"]
        for model in models:
            try:
                return await self._request_with_retry(self._chat_completion, model = model, user_prompt = user_prompt)
            except UpstageClientError as error:
                primary_error = primary_error or error
                if error.status_code not in (429, 500, 502, 503, 504):
                    break
        if primary_error is None:
            raise UpstageClientError("Failed to generate alt text")
        raise primary_error

    async def _request_with_retry(self, func, **options):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await func(**options)
            except UpstageClientError as e:
                if e.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"API 한도 초과(429). {wait_time}초 후 다시 시도합니다. ({attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                raise e

    async def _parse_with_fallback(self, *, image_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
        paths = [self._settings.upstage_parse_path, "/v1/document-parse"]
        first_error: UpstageClientError | None = None
        for path in paths:
            try:
                return await self._request_with_retry(
                    self._request_document_parse,
                    path = path,
                    image_bytes = image_bytes,
                    filename = filename,
                    content_type = content_type,
                )
            except UpstageClientError as error:
                first_error = first_error or error
                if error.status_code not in (404, 405, 429):
                    break
        if first_error is None:
            raise UpstageClientError("Document Parse request failed")
        raise first_error

    async def _request_document_parse(self, *, path: str, image_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
        base_url = self._settings.upstage_base_url.rstrip('/')
        clean_path = f"/{path.lstrip('/')}"
        url = f"{base_url}{clean_path}".replace("/v1/v1", "/v1")
        files = {"document": (filename, image_bytes, content_type)}
        data = {
            "ocr": "auto",
            "output_formats": json.dumps(["markdown", "text"]),
        }
        try:
            response = await self._http.post(url, data = data, files = files, timeout = 15.0)
            if response.status_code >= 400:
                raise UpstageClientError(
                    f"Document Parse failed status {response.status_code}: {response.text}",
                    status_code = response.status_code,
                )
            return response.json()
        except httpx.TimeoutException:
            raise UpstageClientError("Document Parse timed out", status_code = 504)

    async def _chat_completion(self, *, model: str, user_prompt: str) -> str:
        base_url = self._settings.upstage_base_url.rstrip('/')
        clean_path = f"/{self._settings.upstage_chat_path.lstrip('/')}"
        url = f"{base_url}{clean_path}".replace("/v1/v1", "/v1")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        response = await self._http.post(url, json = payload)
        if response.status_code >= 400:
            raise UpstageClientError(
                f"Chat completion failed status {response.status_code}",
                        status_code=response.status_code,
            )
        raw = response.json()
        content = self._extract_chat_content(raw)
        if not content:
            raise UpstageClientError("Empty chat content")
        return self._normalize_alt_text(content)

    def _extract_parse_text(self, payload: dict[str, Any]) -> str:
        for key in ("markdown", "text"):
            value = self._find_first_non_empty_string(payload, key)
            if value: return value
        return ""

    def _extract_chat_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices", [])
        if not choices: return ""
        message = choices[0].get("message", {})
        return message.get("content", "")

    def _find_first_non_empty_string(self, obj: Any, target_key: str) -> str:
        if isinstance(obj, dict):
            direct = obj.get(target_key)
            if isinstance(direct, str) and direct.strip(): return direct
            for value in obj.values():
                nested = self._find_first_non_empty_string(value, target_key)
                if nested: return nested
        elif isinstance(obj, list):
            for item in obj:
                nested = self._find_first_non_empty_string(item, target_key)
                if nested: return nested
        return ""

    def _normalize_alt_text(self, text: str) -> str:
        normalized = " ".join(text.split()).strip()
        if len(normalized) > 320:
            return normalized[:317].rstrip() + "..."
        return normalized
    '''
    async def analyze_full(self, image_bytes, filename, content_type, image_url):
        parsed = await self.parse_document(...)
        alt_text = await self.generate_alt_text(...)
        return alt_text'''