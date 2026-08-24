"""
Interactive Live Reading with Visible Cursor Trails
Opens a visible Chrome browser on your desktop and continuously displays
the glowing virtual mouse cursor moving along text lines, highlighting words,
and scrolling through Confluence in real time.
"""

import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stealth_browser import StealthBrowserLauncher
from core.human_dynamics import HumanKinematics
from core.compliance_reader import ComplianceReadingSimulator

logger = logging.getLogger("InteractiveReader")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")


HIGHLIGHT_TEXT_JS = """
(element) => {
    try {
        const prev = document.querySelectorAll('.agent-reading-highlight');
        prev.forEach(el => el.style.backgroundColor = 'transparent');
        
        element.classList.add('agent-reading-highlight');
        element.style.transition = 'background-color 0.4s ease';
        element.style.backgroundColor = 'rgba(255, 230, 0, 0.35)';
        element.style.borderRadius = '3px';
        element.style.padding = '2px 4px';
    } catch(e) {}
}
"""

CLEAR_HIGHLIGHT_JS = """
() => {
    try {
        const prev = document.querySelectorAll('.agent-reading-highlight');
        prev.forEach(el => {
            el.style.backgroundColor = 'transparent';
        });
    } catch(e) {}
}
"""


async def main():
    target_url = "https://ezai.atlassian.net/wiki/spaces/~712020c417f00f557b4609b0d12ac7aa79e5d8/pages/196706/Getting+started+in+Confluence+from+Jira"
    
    print("\n" + "=" * 70)
    print("👀 STARTING VISIBLE INTERACTIVE HUMAN READING SIMULATION")
    print("=" * 70)
    print("Look at your desktop Chrome window: you will see the glowing red pointer")
    print("gliding across text lines, highlighting paragraphs, and scrolling.\n")

    user_data_dir = os.path.expanduser("~/.atlassian_live_profile")
    launcher = StealthBrowserLauncher(
        headless=False,
        user_data_dir=user_data_dir,
        viewport_width=1440,
        viewport_height=920
    )

    try:
        _, browser, context = await launcher.launch()
        page = await context.new_page()
        page.set_default_timeout(60000)

        kinematics = HumanKinematics(page)
        
        # Navigate to target Confluence page
        print(f"[1/4] Loading Confluence Document:\n  {target_url}\n")
        await page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)
        
        # Synchronize window and inject bright laser cursor
        await kinematics.sync_window_geometry()
        await kinematics.inject_visual_cursor()

        # If on login screen, auto-fill login
        if "id.atlassian.com" in page.url or await page.locator("input#username").count() > 0:
            print("[2/4] Auto-filling login credentials with human cadence...")
            user_input = page.locator("input#username, input[name='username'], input[type='email']").first
            if await user_input.count() > 0:
                box = await user_input.bounding_box()
                if box:
                    await kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await kinematics.human_type("support@ezebld.ai", wpm=80)
                    await asyncio.sleep(0.4)
                    
                    submit_btn = page.locator("#login-submit, button[type='submit']").first
                    if await submit_btn.count() > 0:
                        btn_box = await submit_btn.bounding_box()
                        if btn_box:
                            await kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
                            await asyncio.sleep(2.5)

            pwd_input = page.locator("input#password, input[name='password'], input[type='password']").first
            try:
                await pwd_input.wait_for(state="visible", timeout=6000)
                box = await pwd_input.bounding_box()
                if box:
                    await kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    await kinematics.human_type("2Prosperity026!", wpm=75)
                    await asyncio.sleep(0.4)
                    submit_btn = page.locator("#login-submit, button[type='submit']").first
                    if await submit_btn.count() > 0:
                        btn_box = await submit_btn.bounding_box()
                        if btn_box:
                            await kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
            except Exception:
                pass

            # Wait for landing
            print("  Waiting for landing on document...")
            for _ in range(20):
                if "atlassian.net/wiki" in page.url and "id.atlassian.com" not in page.url:
                    break
                await asyncio.sleep(1.5)

        # Landed on page: Re-inject visual cursor
        await asyncio.sleep(2.0)
        await kinematics.inject_visual_cursor()

        print(f"[3/4] Document Active: '{await page.title()}'")
        print("[4/4] Beginning continuous visible reading simulation...\n")

        # Discover all paragraphs and headings
        headings = await page.locator("h1, h2, h3, p, table, li").all()
        print(f"Found {len(headings)} readable elements on page. Starting human reading loop:\n")

        for idx, element in enumerate(headings[:25], 1):
            try:
                text = (await element.inner_text()).strip()
                if len(text) < 3:
                    continue

                box = await element.bounding_box()
                if not box:
                    continue

                # Scroll element into viewport with smooth animation
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(0.6)

                # Re-calculate box after scroll
                box = await element.bounding_box()
                if not box:
                    continue

                print(f"  📖 Reading [{idx}]: \"{text[:60]}...\"")

                # Move laser cursor to start of line
                start_x = max(100, box["x"] + 20)
                start_y = max(100, box["y"] + box["height"] / 2)
                await kinematics.move_to(start_x, start_y)

                # Highlight line visually with yellow aura
                await element.evaluate(HIGHLIGHT_TEXT_JS)

                # Glide pointer smoothly across the text line
                end_x = min(start_x + box["width"] * 0.8, 1200)
                await kinematics.move_to(end_x, start_y + 5, steps=25)

                # Reading pause proportional to word count
                words = len(text.split())
                dwell = max(2.0, min(words * 0.28, 8.0))
                await asyncio.sleep(dwell)

                # Clear highlight
                await page.evaluate(CLEAR_HIGHLIGHT_JS)

                # 20% chance to simulate a natural mouse click/focus or slight backtrack
                if idx % 4 == 0:
                    print("     ↳ [Human Backtrack]: Scrolling up slightly to re-read...")
                    await kinematics.human_scroll(scroll_delta_y=-180, steps=8)
                    await asyncio.sleep(1.5)
                    await kinematics.human_scroll(scroll_delta_y=190, steps=8)
                    await asyncio.sleep(0.8)

            except Exception as e:
                continue

        print("\n" + "=" * 70)
        print("✅ VISIBLE HUMAN READING SIMULATION COMPLETE")
        print("=" * 70)
        print("Keeping browser window open for 15 seconds so you can inspect...")
        await asyncio.sleep(15.0)

    finally:
        await launcher.close()


if __name__ == "__main__":
    asyncio.run(main())
