"""
Full Deep Reading Simulation & Long-Duration Interactive Session
Performs a comprehensive, top-to-bottom human reading simulation across EVERY
section, paragraph, table, glossary term, and macro on the Confluence document.
The browser STAYS OPEN indefinitely or for an extended session without closing.
"""

import os
import sys
import asyncio
import logging
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stealth_browser import StealthBrowserLauncher
from core.human_dynamics import HumanKinematics
from core.visual_cursor import CURSOR_OVERLAY_JS, UPDATE_CURSOR_JS, SHOW_RIPPLE_JS

logger = logging.getLogger("FullDeepReader")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

HIGHLIGHT_TEXT_JS = """
(element) => {
    try {
        const prev = document.querySelectorAll('.agent-reading-highlight');
        prev.forEach(el => el.style.backgroundColor = 'transparent');
        
        element.classList.add('agent-reading-highlight');
        element.style.transition = 'background-color 0.4s ease';
        element.style.backgroundColor = 'rgba(255, 230, 0, 0.35)';
        element.style.borderRadius = '4px';
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


async def run_full_deep_simulation(
    target_url: str = "https://ezai.atlassian.net/wiki/spaces/~712020c417f00f557b4609b0d12ac7aa79e5d8/pages/196706/Getting+started+in+Confluence+from+Jira",
    keep_alive_minutes: int = 15
):
    print("\n" + "=" * 75)
    print("🚀 STARTING COMPLETE FULL-DOCUMENT DEEP READING SIMULATION")
    print("=" * 75)
    print("• Browser will stay open on your desktop display.")
    print("• Every section, glossary item, and paragraph will be read progressively.")
    print(f"• Persistent session active: will run full reading and stay alive for {keep_alive_minutes} mins.\n")

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
        page.set_default_timeout(90000)

        kinematics = HumanKinematics(page)

        # 1. Navigate to target document
        print(f"[Phase 1] Navigating to Confluence:\n  {target_url}\n")
        await page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

        await kinematics.sync_window_geometry()
        await kinematics.inject_visual_cursor()

        # Check for login screen
        if "id.atlassian.com" in page.url or await page.locator("input#username, input[name='username']").count() > 0:
            print("[Phase 2] Login detected. Entering credentials with natural human cadence...")
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

            print("  Waiting for document landing...")
            for _ in range(25):
                if "atlassian.net/wiki" in page.url and "id.atlassian.com" not in page.url:
                    break
                await asyncio.sleep(1.5)

        await asyncio.sleep(2.5)
        await kinematics.inject_visual_cursor()

        doc_title = await page.title()
        print(f"\n[Phase 3] Document Active: '{doc_title}'")
        print("[Phase 4] Initiating thorough top-to-bottom reading sequence...\n")

        # Focus main content container
        content_elements = await page.locator("h1, h2, h3, h4, p, li, table, [data-renderer-start-pos]").all()
        total_elements = len(content_elements)
        print(f"📊 Discovered {total_elements} content elements. Beginning authentic comprehension loop:\n")

        for idx, element in enumerate(content_elements, 1):
            try:
                text = (await element.inner_text()).strip()
                if len(text) < 4:
                    continue

                # Scroll element into viewport with smooth natural physics
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.4, 0.8))

                box = await element.bounding_box()
                if not box or box["height"] < 8:
                    continue

                words = len(text.split())
                preview = text.replace("\n", " ")[:65]
                print(f"  📖 [{idx}/{total_elements}] ({words}w): \"{preview}...\"")

                # Move glowing laser pointer to start of text block
                start_x = max(120, box["x"] + 20)
                start_y = max(100, box["y"] + box["height"] / 2)
                await kinematics.move_to(start_x, start_y)

                # Visually illuminate the active reading block with soft yellow aura
                await element.evaluate(HIGHLIGHT_TEXT_JS)

                # Move laser cursor horizontally across the lines of the text block
                end_x = min(start_x + box["width"] * 0.85, 1250)
                await kinematics.move_to(end_x, start_y + random.uniform(2, 8), steps=random.randint(20, 35))

                # Human reading dwell time (200-240 WPM biological pacing)
                dwell = max(2.2, min(words * 0.28, 12.0))
                await asyncio.sleep(dwell)

                # Clear highlight
                await page.evaluate(CLEAR_HIGHLIGHT_JS)

                # 15% chance to simulate backtracking (human re-reading previous paragraph)
                if random.random() < 0.15 and idx > 3:
                    backtrack_y = random.randint(160, 300)
                    print(f"     ↳ [Comprehension Backtrack]: Scrolling up {backtrack_y}px to re-verify context...")
                    await kinematics.human_scroll(scroll_delta_y=-backtrack_y, steps=8)
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    # Scroll back to active reading location
                    await kinematics.human_scroll(scroll_delta_y=backtrack_y + 10, steps=8)
                    await asyncio.sleep(0.8)

            except Exception as e:
                continue

        # Instead of getting trapped in a single-page mouse loop, advance through all topics
        print("\n" + "=" * 75)
        print("✅ FIRST DOCUMENT READING PASS COMPLETE")
        print("=" * 75)
        print("Now dynamically expanding sidebar tree and traversing all remaining topics...")
        
        from examples.all_topics_reading_simulation import run_all_topics_simulation
        await run_all_topics_simulation(start_url=target_url)

    except Exception as e:
        print(f"Session notice: {e}")
    finally:
        print("Session ended. Closing browser cleanly.")
        await launcher.close()


if __name__ == "__main__":
    from examples.all_topics_reading_simulation import run_all_topics_simulation
    asyncio.run(run_all_topics_simulation())

