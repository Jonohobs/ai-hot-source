from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


DEFAULT_HEADERS = {
    "User-Agent": "community-scrapes/0.1 (+https://github.com/Jonohobs/community-scrapes)",
    "Accept": "application/json, application/xml, text/xml, */*",
}


def fetch_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 30) -> str:
    request_headers = dict(DEFAULT_HEADERS)
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    return json.loads(fetch_text(url, headers=headers, timeout=timeout))
