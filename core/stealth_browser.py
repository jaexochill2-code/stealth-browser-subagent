"""
Stealth Browser Launcher
Handles hardened browser lifecycle, context isolation, and anti-detection configurations.
Supports rebrowser-playwright, nodriver, and standard Playwright with stealth patches.
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, Tuple

# Configure logger
logger = logging.getLogger("StealthBrowser")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


class StealthBrowserLauncher:
    """Hardened browser launcher preventing CDP and runtime fingerprint leaks."""

    def __init__(
        self,
        headless: bool = False,
        proxy_url: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        self.headless = headless
        self.proxy_url = proxy_url
        self.user_data_dir = user_data_dir
        self.viewport = {"width": viewport_width, "height": viewport_height}
        self.playwright = None
        self.browser = None
        self.context = None

    async def launch(self) -> Tuple[Any, Any, Any]:
        """
        Launches a hardened browser context.
        Attempts rebrowser-playwright first, with fallback to standard Playwright.
        """
        try:
            from rebrowser_playwright.async_api import async_playwright
            logger.info("Using rebrowser-playwright (CDP Runtime.enable leak protected)")
        except ImportError:
            try:
                from playwright.async_api import async_playwright
                logger.info("rebrowser-playwright not installed; falling back to playwright")
            except ImportError:
                raise RuntimeError("Playwright or rebrowser-playwright is required. Run: pip install rebrowser-playwright")

        self.playwright = await async_playwright().start()

        # Modern anti-detection Chromium flags
        chromium_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-component-update",
            "--disable-features=IsolateOrigins,site-per-process,TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-renderer-backgrounding",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            f"--window-size={self.viewport['width']},{self.viewport['height']}",
        ]

        proxy_config = None
        if self.proxy_url:
            proxy_config = {"server": self.proxy_url}

        launch_kwargs = {
            "headless": self.headless,
            "args": chromium_args,
            "proxy": proxy_config,
        }

        # Prefer native system Google Chrome channel if available on host
        if sys.platform == "darwin" and os.path.exists("/Applications/Google Chrome.app"):
            launch_kwargs["channel"] = "chrome"

        self.browser = await self.playwright.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "viewport": self.viewport,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "geolocation": {"longitude": -74.0060, "latitude": 40.7128},
            "permissions": ["geolocation", "notifications"],
            "color_scheme": "dark",
            "device_scale_factor": 1.0,
            "is_mobile": False,
            "has_touch": False,
        }

        self.context = await self.browser.new_context(**context_kwargs)

        # Inject stealth overrides before any document scripts run
        await self.context.add_init_script("""
            // 1. Erase navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 2. Mock chrome runtime object
            window.chrome = {
                app: { isInstalled: false, InstallState: { DISABLED: 'disabled' }, RunningState: { CANNOT_RUN: 'cannot_run' } },
                runtime: {
                    OnInstalledReason: { CHROME_UPDATE: 'chrome_update' },
                    OnRestartRequiredReason: { APP_UPDATE: 'app_update' },
                    PlatformArch: { ARM64: 'arm64', X86_64: 'x86_64' },
                    PlatformNaclArch: { ARM: 'arm', X86_64: 'x86_64' },
                    PlatformOs: { MAC: 'mac', WIN: 'win' },
                    RequestUpdateCheckStatus: { NO_UPDATE: 'no_update' }
                },
                csi: () => {},
                loadTimes: () => {}
            };

            // 3. Normalise navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
                ]
            });

            // 4. Normalise navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        logger.info(f"Stealth browser launched successfully (Headless={self.headless})")
        return self.playwright, self.browser, self.context

    async def close(self):
        """Closes context and browser gracefully."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Stealth browser shut down cleanly.")
