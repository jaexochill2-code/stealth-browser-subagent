"""
WAF & Anti-Bot Challenge Solver
Detects and resolves Cloudflare Turnstile, DataDome, and shadow DOM verification checkboxes.
"""

import asyncio
import logging
from typing import Any, Optional, Tuple
from .human_dynamics import HumanKinematics

logger = logging.getLogger("WAFSolver")


class WAFChallengeSolver:
    """Detects and navigates Cloudflare Turnstile and closed shadow DOM verification challenges."""

    def __init__(self, page: Any, kinematics: HumanKinematics):
        self.page = page
        self.kinematics = kinematics

    async def detect_challenge(self) -> Tuple[bool, str]:
        """Checks if a known WAF challenge or verification widget is active."""
        # 1. Cloudflare Turnstile detection
        title = await self.page.title()
        if "Just a moment..." in title or "Attention Required!" in title:
            return True, "Cloudflare Challenge Page"

        # 2. Check for Turnstile iframes
        for frame in self.page.frames:
            if "challenges.cloudflare.com" in frame.url or "turnstile" in frame.url:
                return True, "Cloudflare Turnstile Iframe"

        # 3. DataDome detection
        if await self.page.locator("iframe[src*='datadome.co'], #datadome-captcha").count() > 0:
            return True, "DataDome Captcha"

        return False, "None"

    async def solve_turnstile_if_present(self, max_attempts: int = 4) -> bool:
        """
        Locates the Turnstile checkbox across iframe and shadow-root boundaries,
        performing a humanized click on the verification target.
        """
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Checking for Turnstile verification (Attempt {attempt}/{max_attempts})...")

            # Search frames for Cloudflare challenge iframe
            target_frame = None
            for frame in self.page.frames:
                if "challenges.cloudflare.com" in frame.url:
                    target_frame = frame
                    break

            if target_frame:
                try:
                    # Look for standard checkbox containers in the challenge frame
                    checkbox = target_frame.locator("input[type='checkbox'], .cb-i, #challenge-stage, label.ctp-checkbox-label")
                    if await checkbox.count() > 0:
                        box = await checkbox.first.bounding_box()
                        if box and box["width"] > 0 and box["height"] > 0:
                            logger.info(f"Turnstile checkbox located at ({box['x']}, {box['y']}). Executing human click.")
                            # Click center of checkbox with humanized movement
                            click_x = box["x"] + box["width"] / 2
                            click_y = box["y"] + box["height"] / 2
                            await self.kinematics.click_at(click_x, click_y)

                            # Wait for challenge validation
                            await asyncio.sleep(2.5)
                            try:
                                await self.page.wait_for_load_state("networkidle", timeout=6000)
                            except Exception:
                                pass

                            # Verify if challenge is cleared
                            is_still_challenging, _ = await self.detect_challenge()
                            if not is_still_challenging:
                                logger.info("Turnstile challenge successfully cleared!")
                                return True
                except Exception as e:
                    logger.warning(f"Error while interacting with Turnstile frame: {e}")

            # Also check main page DOM for shadow root wrapper
            try:
                turnstile_wrapper = self.page.locator("#turnstile-wrapper, [data-sitekey]")
                if await turnstile_wrapper.count() > 0:
                    box = await turnstile_wrapper.first.bounding_box()
                    if box:
                        await self.kinematics.click_at(box["x"] + 25, box["y"] + 25)
                        await asyncio.sleep(2.0)
            except Exception:
                pass

            await asyncio.sleep(1.5)

        logger.info("No active Turnstile challenge detected or already passed.")
        return False
