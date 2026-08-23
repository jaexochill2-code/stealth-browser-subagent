"""
Live Visible Browser Reading Simulation
Opens a visible Google Chrome / Chromium window on your macOS screen so you can watch
the mouse cursor move along Bézier curves, text highlight, and scroll in real-time.
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

logger = logging.getLogger("LiveVisualReader")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


async def main():
    target_url = "https://ezai.atlassian.net/wiki/spaces/~712020c417f00f557b4609b0d12ac7aa79e5d8/pages/196706/Getting+started+in+Confluence+from+Jira"
    email = "support@ezebld.ai"
    password = "2Prosperity026!"

    print("\n" + "=" * 65)
    print("🚀 LAUNCHING VISIBLE CHROME BROWSER ON YOUR MACOS DESKTOP...")
    print("=" * 65)

    user_data_dir = os.path.expanduser("~/.atlassian_live_profile")
    # Headless=False opens a real GUI window on your desktop
    launcher = StealthBrowserLauncher(
        headless=False,
        user_data_dir=user_data_dir,
        viewport_width=1400,
        viewport_height=900
    )

    try:
        _, browser, context = await launcher.launch()
        page = await context.new_page()
        page.set_default_timeout(60000)

        kinematics = HumanKinematics(page)
        await kinematics.sync_window_geometry()
        waf_solver = WAFChallengeSolver(page, kinematics)
        reader = ComplianceReadingSimulator(page, kinematics)

        print(f"\n[Step 1] Navigating to Confluence Document:\n  {target_url}\n")
        await page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(2.0)

        # 1. Check if Atlassian login is required
        if "id.atlassian.com" in page.url or await page.locator("input#username, input[name='username']").count() > 0:
            print("[Step 2] Atlassian Login Screen detected. Typing credentials with biological dynamics...")
            user_input = page.locator("input#username, input[name='username'], input[type='email']").first
            if await user_input.count() > 0:
                box = await user_input.bounding_box()
                if box:
                    await kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await kinematics.human_type(email, wpm=85)
                    await asyncio.sleep(0.5)

                submit_btn = page.locator("#login-submit, button[type='submit']").first
                if await submit_btn.count() > 0:
                    btn_box = await submit_btn.bounding_box()
                    if btn_box:
                        await kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
                        await asyncio.sleep(2.5)

            # Enter password if visible
            pwd_input = page.locator("input#password, input[name='password'], input[type='password']").first
            try:
                await pwd_input.wait_for(state="visible", timeout=6000)
                box = await pwd_input.bounding_box()
                if box:
                    await kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await kinematics.human_type(password, wpm=80)
                    await asyncio.sleep(0.5)

                    submit_btn = page.locator("#login-submit, button[type='submit']").first
                    if await submit_btn.count() > 0:
                        btn_box = await submit_btn.bounding_box()
                        if btn_box:
                            await kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
            except Exception:
                print("  Note: Password field skipped or redirected.")

            # Wait for landing on target document
            print("  Waiting for landing on target Confluence page (complete any on-screen prompt if shown)...")
            for _ in range(25):
                if "atlassian.net/wiki" in page.url and "id.atlassian.com" not in page.url:
                    break
                await asyncio.sleep(2.0)

        # 2. Perform live visual human reading
        print("\n[Step 3] Document loaded! Starting live human reading simulation...")
        print("  • Watch your screen: cursor movements, scrolling, and section dwell times are active.\n")
        
        result = await reader.read_entire_document(
            min_total_reading_minutes=1.5,
            backtrack_probability=0.20
        )

        print("\n" + "=" * 65)
        print("✅ LIVE COMPLIANCE READING COMPLETE")
        print("=" * 65)
        print(f"Document Title:     {await page.title()}")
        print(f"Total Dwell Time:   {result['dwell_time_minutes']} minutes")
        print(f"Blocks Read:        {result['total_blocks_read']}")
        print(f"Reading Speed:      {result['reading_wpm_profile']} WPM")
        print("=" * 65 + "\n")

        # Keep browser open for 5 seconds so you can see final state
        await asyncio.sleep(5.0)

    finally:
        await launcher.close()


if __name__ == "__main__":
    asyncio.run(main())
