"""
Fast HTTP Harvesting Client (curl_cffi)
Implements the "Browser Solve -> Fast Client Harvest" pipeline.
Imports clearance cookies (cf_clearance) and headers from the hardened browser,
executing high-throughput requests at native C-speed with real Chrome TLS JA4 signatures.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("FastClient")

try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    logger.warning("curl_cffi is not installed. Run: pip install curl_cffi")


class FastHarvestClient:
    """High-speed HTTP client with Chrome 130+ TLS/JA4 fingerprint matching."""

    def __init__(
        self,
        impersonate: str = "chrome131",
        proxy_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.impersonate = impersonate
        self.proxy_url = proxy_url
        self.headers = headers or {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        self.session: Optional[Any] = None

    async def init_from_browser_context(self, context: Any):
        """Extracts cookies and local state from an active Playwright browser context."""
        if not CURL_CFFI_AVAILABLE:
            raise RuntimeError("curl_cffi is required for FastHarvestClient. Run: pip install curl_cffi")

        cookies_list = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies_list}

        proxies = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else None

        self.session = AsyncSession(
            impersonate=self.impersonate,
            headers=self.headers,
            cookies=cookie_dict,
            proxies=proxies
        )

        has_cf = "cf_clearance" in cookie_dict
        logger.info(f"FastHarvestClient initialized with {len(cookie_dict)} cookies (cf_clearance={has_cf}).")

    async def get(self, url: str, **kwargs) -> Any:
        """Executes a high-speed GET request with Chrome TLS fingerprinting."""
        if not self.session:
            proxies = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else None
            self.session = AsyncSession(impersonate=self.impersonate, headers=self.headers, proxies=proxies)
        return await self.session.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> Any:
        """Executes a high-speed POST request with Chrome TLS fingerprinting."""
        if not self.session:
            proxies = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else None
            self.session = AsyncSession(impersonate=self.impersonate, headers=self.headers, proxies=proxies)
        return await self.session.post(url, **kwargs)

    async def close(self):
        """Closes the async session."""
        if self.session:
            await self.session.close()
            logger.info("FastHarvestClient closed.")
