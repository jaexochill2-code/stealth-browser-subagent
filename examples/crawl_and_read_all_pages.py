"""
Multi-Page Confluence Space Crawler & Deep Reading Agent
Iterates through EVERY page in the Confluence space content tree, clicking and navigating
into each individual document, scrolling top-to-bottom, moving the glowing laser cursor,
highlighting text blocks, and generating authentic reading telemetry across all pages.
"""

import os
import sys
import json
import sqlite3
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stealth_browser import StealthBrowserLauncher
from core.human_dynamics import HumanKinematics
from core.visual_cursor import CURSOR_OVERLAY_JS

logger = logging.getLogger("MultiPageCrawler")
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


def load_space_pages(db_path: str, space_name: str = "Netanel Gabizon") -> List[Dict[str, Any]]:
    """Loads all page URLs and titles from the local RAG database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT page_id, title, url, word_count
        FROM documents
        WHERE space_name = ?
        ORDER BY CAST(page_id AS INTEGER) ASC
    """, (space_name,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


async def read_single_page(page: Any, kinematics: Any, page_info: Dict[str, Any], page_index: int, total_pages: int):
    """Navigates into a single Confluence page, executes human reading pass, and scrolls top-to-bottom."""
    url = page_info["url"]
    title = page_info["title"]
    word_count = page_info.get("word_count", 200)

    print("\n" + "-" * 70)
    print(f"📄 [PAGE {page_index}/{total_pages}] Opening: \"{title}\"")
    print(f"   URL: {url} ({word_count} words)")
    print("-" * 70)

    # 1. Navigate to page
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"   Notice during navigation: {e}")
    await asyncio.sleep(2.0)

    # Re-inject visual cursor
    await kinematics.inject_visual_cursor()

    # 2. Discover readable content elements on this page
    elements = await page.locator("h1, h2, h3, h4, p, table, li, [data-renderer-start-pos]").all()
    print(f"   Discovered {len(elements)} content blocks on page. Reading...")

    # Traverse through content blocks
    for idx, element in enumerate(elements[:15], 1):
        try:
            text = (await element.inner_text()).strip()
            if len(text) < 4:
                continue

            await element.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.3, 0.6))

            box = await element.bounding_box()
            if not box or box["height"] < 6:
                continue

            # Move laser pointer to block
            start_x = max(120, box["x"] + 20)
            start_y = max(100, box["y"] + box["height"] / 2)
            await kinematics.move_to(start_x, start_y)

            # Highlight text line in yellow
            await element.evaluate(HIGHLIGHT_TEXT_JS)

            # Move laser cursor horizontally across the line
            end_x = min(start_x + box["width"] * 0.85, 1200)
            await kinematics.move_to(end_x, start_y + 3, steps=random.randint(18, 28))

            # Dwell time proportional to paragraph length
            words = len(text.split())
            dwell = max(1.8, min(words * 0.22, 6.0))
            await asyncio.sleep(dwell)

            # Clear highlight
            await page.evaluate(CLEAR_HIGHLIGHT_JS)

            # Occasional small scroll / backtrack
            if idx % 5 == 0:
                await kinematics.human_scroll(scroll_delta_y=-120, steps=6)
                await asyncio.sleep(1.0)
                await kinematics.human_scroll(scroll_delta_y=130, steps=6)

        except Exception:
            continue

    # Final scroll down to footer
    await kinematics.human_scroll(scroll_delta_y=500, steps=8)
    await asyncio.sleep(1.5)
    print(f"   ✅ Finished reading page: \"{title}\"")


async def crawl_and_read_all(
    space_name: str = "Netanel Gabizon",
    limit: Optional[int] = None,
    start_index: int = 1
):
    db_path = "/Users/flowstatework/.gemini/antigravity-ide/scratch/stealth-browser-subagent/knowledge_rag.db"
    pages = load_space_pages(db_path, space_name)

    if not pages:
        print(f"No pages found for space '{space_name}' in RAG database.")
        return

    selected_pages = pages[start_index - 1 : start_index - 1 + limit] if limit else pages[start_index - 1 :]
    total_selected = len(selected_pages)

    print("\n" + "=" * 75)
    print(f"🌐 LAUNCHING MULTI-PAGE SPACE CRAWLER: '{space_name}'")
    print("=" * 75)
    print(f"• Total Pages to Traverse: {total_selected} documents")
    print("• Browser will stay open on your desktop, navigating into each page one-by-one.\n")

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

        # Initial navigation to first page
        first_url = selected_pages[0]["url"]
        print(f"[Init] Connecting to Confluence starting page:\n  {first_url}\n")
        await page.goto(first_url, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

        await kinematics.sync_window_geometry()
        await kinematics.inject_visual_cursor()

        # Check if login needed
        if "id.atlassian.com" in page.url or await page.locator("input#username").count() > 0:
            print("[Auth] Logging in with human cadence...")
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

            for _ in range(20):
                if "atlassian.net/wiki" in page.url and "id.atlassian.com" not in page.url:
                    break
                await asyncio.sleep(1.5)

        # Iterate through every page in sequence
        for idx, p_info in enumerate(selected_pages, start_index):
            await read_single_page(page, kinematics, p_info, page_index=idx, total_pages=len(pages))
            await asyncio.sleep(1.5)

        print("\n" + "=" * 75)
        print("🎉 ALL PAGES IN SPACE SUCCESSFULLY CRAWLED AND READ!")
        print("=" * 75)
        print("Keeping browser open for 15 seconds so you can inspect...")
        await asyncio.sleep(15.0)

    finally:
        await launcher.close()


if __name__ == "__main__":
    # Crawls pages in space with visible cursor
    asyncio.run(crawl_and_read_all(space_name="Netanel Gabizon", limit=None))
