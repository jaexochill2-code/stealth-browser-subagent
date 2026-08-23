"""
Autonomous Browsing & Form-Filling Subagent (Enhanced)
Integrates hardened browser execution, visual perception, WAF challenge handling,
human dynamics, and high-speed curl_cffi session handoff into a unified autonomous agent.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional

from core.stealth_browser import StealthBrowserLauncher
from core.human_dynamics import HumanKinematics
from core.perception import VisualPerceptionEngine
from core.waf_solver import WAFChallengeSolver
from core.form_agent import FormFillEngine
from core.fast_client import FastHarvestClient

logger = logging.getLogger("AutonomousSubagent")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")


class AutonomousBrowsingSubagent:
    """End-to-end subagent for stealth web navigation, understanding, and form execution."""

    def __init__(
        self,
        headless: bool = False,
        proxy_url: Optional[str] = None,
        timeout_ms: int = 30000
    ):
        self.proxy_url = proxy_url
        self.launcher = StealthBrowserLauncher(headless=headless, proxy_url=proxy_url)
        self.timeout_ms = timeout_ms
        self.browser = None
        self.context = None
        self.page = None
        self.kinematics = None
        self.perception = None
        self.waf_solver = None
        self.form_engine = None

    async def start(self):
        """Initializes the browser and connects all subagent perception/execution engines."""
        logger.info("Initializing Autonomous Browsing Subagent...")
        _, self.browser, self.context = await self.launcher.launch()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)

        self.kinematics = HumanKinematics(self.page)
        await self.kinematics.sync_window_geometry()

        self.perception = VisualPerceptionEngine(self.page)
        self.waf_solver = WAFChallengeSolver(self.page, self.kinematics)
        self.form_engine = FormFillEngine(self.page, self.kinematics)
        logger.info("Subagent initialized and ready for navigation.")

    async def navigate_and_fill(
        self,
        url: str,
        form_data: Dict[str, Any],
        auto_submit: bool = False,
        screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Navigates to URL, bypasses WAF/Turnstile challenges if present,
        extracts page state, fills matching form fields, and captures verification artifacts.
        """
        if not self.page:
            await self.start()

        logger.info(f"Navigating to target URL: {url}")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        except Exception as e:
            logger.warning(f"Initial navigation completed with notice: {e}")

        # Natural page settlement delay
        await asyncio.sleep(2.0)

        # 1. Check and resolve WAF / Cloudflare Turnstile challenges
        is_challenge, challenge_type = await self.waf_solver.detect_challenge()
        if is_challenge:
            logger.warning(f"Active challenge detected: '{challenge_type}'. Initiating bypass sequence...")
            await self.waf_solver.solve_turnstile_if_present()

        # 2. Extract visual perception and interactive element coordinates
        base64_screenshot, elements = await self.perception.capture_state()

        # 3. Perform semantic form filling
        fill_results = await self.form_engine.fill_form(
            elements=elements,
            payload=form_data,
            auto_submit=auto_submit
        )

        # 4. Capture final verification screenshot if requested
        if screenshot_path:
            os.makedirs(os.path.dirname(os.path.abspath(screenshot_path)), exist_ok=True)
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Verification screenshot saved to: {screenshot_path}")

        page_title = await self.page.title()
        current_url = self.page.url

        return {
            "title": page_title,
            "url": current_url,
            "challenge_encountered": is_challenge,
            "fill_results": fill_results,
            "elements_detected": len(elements)
        }

    async def export_fast_client(self) -> FastHarvestClient:
        """
        Exports the cleared cookies and active session into a high-speed curl_cffi client
        for 100x faster subsequent requests using matching Chrome TLS JA4 signatures.
        """
        if not self.context:
            raise RuntimeError("Browser context is not initialized.")

        client = FastHarvestClient(proxy_url=self.proxy_url)
        await client.init_from_browser_context(self.context)
        return client

    async def stop(self):
        """Clean shutdown of browser context and subagent workers."""
        if self.launcher:
            await self.launcher.close()
        logger.info("Autonomous Browsing Subagent stopped.")
