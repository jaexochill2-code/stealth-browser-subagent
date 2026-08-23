"""
Atlassian Stealth Browser Subagent
Automates browser navigation across Confluence and Jira, handles interactive logins,
bypasses anti-bot friction, and extracts shared spaces, pages, and ticket roadmaps.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional

from .stealth_browser import StealthBrowserLauncher
from .human_dynamics import HumanKinematics
from .perception import VisualPerceptionEngine
from .waf_solver import WAFChallengeSolver

logger = logging.getLogger("AtlassianBrowser")


class AtlassianBrowserSubagent:
    """Specialized stealth subagent for interactive Atlassian browsing and document extraction."""

    def __init__(
        self,
        domain: str,
        headless: bool = False,
        user_data_dir: Optional[str] = None
    ):
        domain = domain.strip().rstrip("/")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        if not domain.endswith(".atlassian.net") and "atlassian.net" not in domain:
            domain = f"{domain}.atlassian.net"

        self.domain = domain
        self.headless = headless
        self.user_data_dir = user_data_dir or os.path.expanduser("~/.atlassian_browser_session")
        self.launcher = StealthBrowserLauncher(headless=self.headless, user_data_dir=self.user_data_dir)
        self.page = None
        self.context = None
        self.browser = None
        self.kinematics = None
        self.perception = None
        self.waf_solver = None

    async def start(self):
        """Launches the stealth browser instance."""
        logger.info(f"Starting Atlassian Browser Subagent for {self.domain} (Headless={self.headless})...")
        _, self.browser, self.context = await self.launcher.launch()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(45000)

        self.kinematics = HumanKinematics(self.page)
        await self.kinematics.sync_window_geometry()
        self.perception = VisualPerceptionEngine(self.page)
        self.waf_solver = WAFChallengeSolver(self.page, self.kinematics)

    async def login(self, email: str, password: Optional[str] = None, wait_for_mfa_seconds: int = 60) -> bool:
        """
        Navigates to Atlassian login and enters email/password.
        If 2FA / SSO / Google sign-in is required, pauses for user approval.
        """
        login_url = f"https://id.atlassian.com/login?continue={self.domain}"
        logger.info(f"Navigating to login URL: {login_url}")
        await self.page.goto(login_url, wait_until="domcontentloaded")
        await asyncio.sleep(2.0)

        # Check for Cloudflare challenge
        is_chal, chal_type = await self.waf_solver.detect_challenge()
        if is_chal:
            logger.info(f"Resolving challenge: {chal_type}")
            await self.waf_solver.solve_turnstile_if_present()

        # Type username/email
        email_input = self.page.locator("input#username, input[name='username'], input[type='email']").first
        if await email_input.count() > 0:
            logger.info(f"Entering email: {email}")
            box = await email_input.bounding_box()
            if box:
                await self.kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                await self.kinematics.human_type(email)
                await asyncio.sleep(0.5)

                # Click continue button
                submit_btn = self.page.locator("#login-submit, button[type='submit']").first
                if await submit_btn.count() > 0:
                    btn_box = await submit_btn.bounding_box()
                    if btn_box:
                        await self.kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
                        await asyncio.sleep(2.5)

        # If password is provided and password input appears
        if password:
            pwd_input = self.page.locator("input#password, input[name='password'], input[type='password']").first
            try:
                await pwd_input.wait_for(state="visible", timeout=6000)
                logger.info("Entering password...")
                box = await pwd_input.bounding_box()
                if box:
                    await self.kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await self.kinematics.human_type(password)
                    await asyncio.sleep(0.5)

                    submit_btn = self.page.locator("#login-submit, button[type='submit']").first
                    if await submit_btn.count() > 0:
                        btn_box = await submit_btn.bounding_box()
                        if btn_box:
                            await self.kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
            except Exception:
                logger.info("Password field not immediately visible (may be SSO / Google OAuth redirected).")

        # Wait for redirect to target domain or completion of MFA
        logger.info(f"Waiting up to {wait_for_mfa_seconds}s for authentication completion...")
        for _ in range(wait_for_mfa_seconds // 2):
            curr_url = self.page.url
            if "atlassian.net" in curr_url and "id.atlassian.com" not in curr_url:
                logger.info(f"Successfully authenticated and redirected to: {curr_url}")
                return True
            await asyncio.sleep(2.0)

        return "id.atlassian.com" not in self.page.url

    async def browse_and_extract_confluence(self, output_dir: str = "./extracted_confluence") -> List[Dict[str, Any]]:
        """Navigates to Confluence, discovers pages and shared docs, and extracts contents."""
        wiki_url = f"{self.domain}/wiki/home"
        logger.info(f"Navigating to Confluence: {wiki_url}")
        await self.page.goto(wiki_url, wait_until="networkidle")
        await asyncio.sleep(3.0)

        os.makedirs(output_dir, exist_ok=True)
        # Extract page title and main text content
        content_data = await self.page.evaluate("""
            () => {
                const title = document.title;
                const mainContent = document.querySelector('main, #main, #main-content, .ak-main-content') || document.body;
                const links = Array.from(document.querySelectorAll('a[href*="/wiki/spaces/"]')).map(a => ({
                    title: a.innerText.trim(),
                    href: a.href
                })).filter(l => l.title.length > 0);

                return {
                    title: title,
                    text: mainContent.innerText,
                    links: links
                };
            }
        """)

        logger.info(f"Extracted Confluence Home: '{content_data.get('title')}' with {len(content_data.get('links', []))} space/page links.")
        return [content_data]

    async def close(self):
        """Closes browser session."""
        if self.launcher:
            await self.launcher.close()
