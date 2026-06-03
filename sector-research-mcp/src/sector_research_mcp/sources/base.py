"""Shared HTTP helpers for source clients.

Every client returns a uniform envelope: ``{"ok": bool, ...}``. Errors never
raise out of a tool — they come back as ``{"ok": False, "error": "..."}`` so the
calling model can decide whether to fall back to another source.
"""

from __future__ import annotations

from typing import Any

import httpx

from .. import config


def err(message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "error": message, **extra}


def ok(**data: Any) -> dict[str, Any]:
    return {"ok": True, **data}


async def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Perform an HTTP request and decode JSON, normalizing failures."""
    timeout = timeout or config.HTTP_TIMEOUT_SECONDS
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.request(
                method, url, headers=headers, params=params, json=json
            )
    except httpx.HTTPError as exc:
        return err(f"request failed: {exc!s}", url=url)

    if resp.status_code >= 400:
        body = resp.text[:500]
        return err(
            f"HTTP {resp.status_code} from {url}",
            status_code=resp.status_code,
            body=body,
        )
    try:
        return ok(status_code=resp.status_code, data=resp.json())
    except ValueError:
        return ok(status_code=resp.status_code, text=resp.text[:20000])


async def request_text(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float | None = None,
    max_chars: int = 40_000,
) -> dict[str, Any]:
    """GET a URL and return truncated text (used for keyless page fetches)."""
    timeout = timeout or config.HTTP_TIMEOUT_SECONDS
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers, params=params)
    except httpx.HTTPError as exc:
        return err(f"request failed: {exc!s}", url=url)
    if resp.status_code >= 400:
        return err(f"HTTP {resp.status_code} from {url}", status_code=resp.status_code)
    return ok(status_code=resp.status_code, text=resp.text[:max_chars])
