from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote_plus


class CachedHttpClient:
    def __init__(
        self,
        cache_dir: Path | str | None = None,
        min_delay_seconds: float = 2.5,
        timeout_seconds: float = 20.0,
        user_agent: str = "ai-hot-sauce-mcpmarket-scraper/0.1",
    ) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.min_delay_seconds = min_delay_seconds
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self._last_request_at = 0.0
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path_for(self, url: str) -> Path | None:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{quote_plus(url)}.html"

    def fetch_text(self, url: str, force: bool = False) -> str:
        cache_path = self._cache_path_for(url)
        if cache_path and cache_path.exists() and not force:
            return cache_path.read_text(encoding="utf-8")

        sleep_for = self.min_delay_seconds - (time.time() - self._last_request_at)
        if sleep_for > 0:
            time.sleep(sleep_for)

        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = response.read().decode("utf-8", errors="ignore")
                self._last_request_at = time.time()
                if cache_path:
                    cache_path.write_text(payload, encoding="utf-8")
                return payload
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code != 429 or attempt == 2:
                    raise
                time.sleep((attempt + 1) * 5)
            except Exception as exc:  # pragma: no cover
                last_error = exc
                if attempt == 2:
                    raise
                time.sleep((attempt + 1) * 2)
        if last_error:
            raise last_error
        raise RuntimeError(f"Failed to fetch {url}")
