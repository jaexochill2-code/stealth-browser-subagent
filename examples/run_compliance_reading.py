"""
Compliance Reading Execution Workflow
Runs a fully simulated, telemetry-compliant reading session on any target URL,
generating authentic dwell times, scroll heatmaps, and pointer tracking logs.
"""

import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stealth_browser import StealthBrowserLauncher
from core.human_dynamics import HumanKinematics
from core.waf_solver import WAFChallengeSolver
from core.compliance_reader import ComplianceReadingSimulator

logger = logging.getLogger("ComplianceRunner")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


async def execute_compliance_read(
    target_url: str,
    min_reading_minutes: float = 2.0,
    headless: bool = True
):
    """Executes a fully simulated reading session."""
    user_data_dir = os.path.expanduser("~/.atlassian_browser_profile")
    launcher = StealthBrowserLauncher(headless=headless, user_data_dir=user_data_dir)
    
    try:
        _, browser, context = await launcher.launch()
        page = await context.new_page()
        page.set_default_timeout(45000)

        kinematics = HumanKinematics(page)
        await kinematics.sync_window_geometry()
        waf_solver = WAFChallengeSolver(page, kinematics)
        reader = ComplianceReadingSimulator(page, kinematics)

        logger.info(f"Navigating to document: {target_url}")
        await page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(2.5)

        # Handle any initial challenge
        is_chal, _ = await waf_solver.detect_challenge()
        if is_chal:
            await waf_solver.solve_turnstile_if_present()

        # Execute the human compliance reading simulation
        result = await reader.read_entire_document(
            min_total_reading_minutes=min_reading_minutes,
            backtrack_probability=0.18
        )

        print("\n=== COMPLIANCE READING REPORT ===")
        print(f"Target Document:     {await page.title()}")
        print(f"URL:                 {page.url}")
        print(f"Blocks/Sections:     {result['total_blocks_read']}")
        print(f"Verified Dwell Time: {result['dwell_time_minutes']} minutes")
        print(f"Reading Speed:       {result['reading_wpm_profile']} WPM (Gaussian Paced)")
        print(f"Status:              {result['status']}")

    finally:
        await launcher.close()


if __name__ == "__main__":
    url = "https://ezai.atlassian.net/wiki/spaces/~712020c417f00f557b4609b0d12ac7aa79e5d8/pages/196706/Getting+started+in+Confluence+from+Jira"
    asyncio.run(execute_compliance_read(url, min_reading_minutes=2.0, headless=True))
