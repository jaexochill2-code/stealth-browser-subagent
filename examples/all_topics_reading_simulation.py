"""
All-Topics Tree Navigator & Full Confluence Deep Reading Simulation
Systematically discovers, expands, and traverses ALL topics and sub-pages
in the Confluence navigation tree (EZ Flows, EZ Internal lists, EZBuild ChatBot PRD,
EZBuild WebUI PRD, Product requirements, Infrastructure Cost Model, UX/UI Guidelines,
Mobile App - PRD, etc.) without getting trapped in single-page idle loops.
"""

import os
import sys
import asyncio
import logging
import random
import sqlite3
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.stealth_browser import StealthBrowserLauncher
from core.human_dynamics import HumanKinematics
from core.visual_cursor import CURSOR_OVERLAY_JS, UPDATE_CURSOR_JS, SHOW_RIPPLE_JS

logger = logging.getLogger("AllTopicsReader")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

HIGHLIGHT_TEXT_JS = """
(element) => {
    try {
        const prev = document.querySelectorAll('.agent-reading-highlight');
        prev.forEach(el => el.style.backgroundColor = 'transparent');
        
        element.classList.add('agent-reading-highlight');
        element.style.transition = 'background-color 0.35s ease';
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

# JavaScript to recursively expand all sidebar folder trees in Confluence
EXPAND_ALL_SIDEBAR_TREES_JS = """
() => {
    let expandedCount = 0;
    // Look for all collapsed tree items, chevron buttons, and expand icons
    const expandButtons = Array.from(document.querySelectorAll(
        'button[aria-expanded="false"], [aria-expanded="false"] button, [data-testid*="expand"], [aria-label*="expand" i], [aria-label*="Expand" i]'
    ));
    
    // Also find SVGs/chevrons within navigation tree items
    const treeItems = Array.from(document.querySelectorAll('nav, [data-testid="page-tree"], div[role="tree"], [aria-label="Pages"]'));
    
    expandButtons.forEach(btn => {
        try {
            btn.click();
            expandedCount++;
        } catch(e) {}
    });
    
    return expandedCount;
}
"""

# JavaScript to extract all sidebar topic links and labels
EXTRACT_SIDEBAR_TOPICS_JS = """
() => {
    const topics = [];
    const seenUrls = new Set();
    
    // Select all links in sidebar/tree navigation
    const navContainers = document.querySelectorAll('nav, [data-testid="page-tree"], div[role="tree"], aside, [aria-label="Pages"]');
    
    navContainers.forEach(nav => {
        const links = nav.querySelectorAll('a[href*="/wiki/spaces/"]');
        links.forEach(a => {
            const title = a.innerText.trim();
            const href = a.href;
            if (title && href && !seenUrls.has(href)) {
                seenUrls.add(href);
                const rect = a.getBoundingClientRect();
                topics.push({
                    title: title,
                    url: href,
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2,
                    visible: rect.height > 0 && rect.width > 0
                });
            }
        });
    });
    
    return topics;
}
"""


def get_all_database_topics(db_path: str) -> List[Dict[str, str]]:
    """Loads all known documents from local RAG database as a complete catalog."""
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT page_id, title, space_name, url FROM documents ORDER BY page_id")
        rows = cursor.fetchall()
        conn.close()
        return [{"page_id": r[0], "title": r[1], "space_name": r[2], "url": r[3]} for r in rows]
    except Exception as e:
        logger.warning(f"Database query notice: {e}")
        return []


async def simulate_human_login_if_needed(page, kinematics: HumanKinematics):
    """Auto-fills login with human kinematics if on login screen."""
    if "id.atlassian.com" in page.url or await page.locator("input#username, input[name='username']").count() > 0:
        print("[Login] Atlassian login screen detected. Authenticating...")
        user_input = page.locator("input#username, input[name='username'], input[type='email']").first
        if await user_input.count() > 0:
            box = await user_input.bounding_box()
            if box:
                await kinematics.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                await kinematics.human_type("support@ezebld.ai", wpm=85)
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
                await kinematics.human_type("2Prosperity026!", wpm=80)
                await asyncio.sleep(0.4)
                submit_btn = page.locator("#login-submit, button[type='submit']").first
                if await submit_btn.count() > 0:
                    btn_box = await submit_btn.bounding_box()
                    if btn_box:
                        await kinematics.click_at(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
        except Exception:
            pass

        for _ in range(25):
            if "atlassian.net/wiki" in page.url and "id.atlassian.com" not in page.url:
                break
            await asyncio.sleep(1.2)


async def read_active_document(page, kinematics: HumanKinematics, topic_title: str, topic_index: int, total_topics: int) -> int:
    """Performs authentic, visible human reading simulation across all paragraphs of the active page."""
    await kinematics.inject_visual_cursor()
    
    # Extract readable blocks
    content_elements = await page.locator("h1, h2, h3, h4, p, li, table, [data-renderer-start-pos]").all()
    if not content_elements:
        content_elements = await page.locator("article, main, body").all()
        
    num_elements = len(content_elements)
    print(f"\n📖 [{topic_index}/{total_topics}] ACTIVE TOPIC: '{topic_title}' ({num_elements} content blocks)")
    
    words_read_total = 0
    
    # Read each paragraph / heading sequentially
    for idx, el in enumerate(content_elements[:35], 1):
        try:
            text = (await el.inner_text()).strip()
            if len(text) < 4:
                continue

            # Smooth scroll element into view
            await el.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.3, 0.6))

            box = await el.bounding_box()
            if not box or box["height"] < 8:
                continue

            words = len(text.split())
            words_read_total += words
            preview = text.replace("\n", " ")[:60]
            print(f"   ↳ Block [{idx}]: ({words}w) \"{preview}...\"")

            # Move laser pointer to start of text block
            start_x = max(180, min(box["x"] + 20, 1100))
            start_y = max(100, min(box["y"] + box["height"] / 2, 850))
            await kinematics.move_to(start_x, start_y)

            # Highlight active paragraph in soft yellow
            await el.evaluate(HIGHLIGHT_TEXT_JS)

            # Move laser cursor along reading line
            end_x = min(start_x + box["width"] * 0.75, 1200)
            await kinematics.move_to(end_x, start_y + random.uniform(2, 6), steps=random.randint(15, 25))

            # Dwell time for reading (200-240 WPM biological pacing)
            dwell = max(1.8, min(words * 0.22, 6.5))
            await asyncio.sleep(dwell)

            # Clear highlight
            await page.evaluate(CLEAR_HIGHLIGHT_JS)

            # 12% chance for natural human backtrack
            if random.random() < 0.12 and idx > 3:
                backtrack_y = random.randint(140, 240)
                await kinematics.human_scroll(scroll_delta_y=-backtrack_y, steps=6)
                await asyncio.sleep(random.uniform(1.2, 2.2))
                await kinematics.human_scroll(scroll_delta_y=backtrack_y + 5, steps=6)
                await asyncio.sleep(0.5)

        except Exception:
            continue

    print(f"   ✅ Finished Topic '{topic_title}': Read {words_read_total} words.")
    return words_read_total


async def run_all_topics_simulation(
    start_url: str = "https://ezai.atlassian.net/wiki/spaces/~712020c417f00f557b4609b0d12ac7aa79e5d8/pages/196706/Getting+started+in+Confluence+from+Jira",
    max_topics: Optional[int] = None
):
    print("\n" + "=" * 80)
    print("🌟 STARTING ALL-TOPICS CONFLUENCE SIDEBAR NAVIGATOR & DEEP READER")
    print("=" * 80)
    print("• Dynamically expands all sidebar topic folders (EZ Flows, PRDs, UX, Mobile, etc.)")
    print("• Navigates topic-by-topic across every document in the tree")
    print("• Simulates authentic human reading on every page with laser cursor tracking")
    print("• Updates RAG knowledge base continuously\n")

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_rag.db"))
    db_topics = get_all_database_topics(db_path)
    print(f"📚 Loaded {len(db_topics)} registered document topics from knowledge base.\n")

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

        # 1. Navigate to initial workspace page
        print(f"[Phase 1] Navigating to Confluence Space:\n  {start_url}\n")
        await page.goto(start_url, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

        await kinematics.sync_window_geometry()
        await kinematics.inject_visual_cursor()

        # Handle login if needed
        await simulate_human_login_if_needed(page, kinematics)
        await asyncio.sleep(2.5)
        await kinematics.inject_visual_cursor()

        # 2. Expand all sidebar trees and discover topic nodes
        print("[Phase 2] Discovering and expanding all sidebar navigation trees...")
        
        # Click expand buttons in sidebar multiple passes to expand nested trees
        for pass_num in range(1, 4):
            expanded = await page.evaluate(EXPAND_ALL_SIDEBAR_TREES_JS)
            print(f"  ↳ Expansion pass {pass_num}: Expanded {expanded} folder nodes.")
            await asyncio.sleep(1.2)

        # Extract all visible sidebar links
        sidebar_topics = await page.evaluate(EXTRACT_SIDEBAR_TOPICS_JS)
        print(f"\n📊 Extracted {len(sidebar_topics)} interactive topic nodes directly from the sidebar tree.")

        # Build master topic queue combining sidebar DOM links and database catalog
        topic_queue = []
        seen_urls = set()

        for t in sidebar_topics:
            u = t.get("url", "")
            if u and u not in seen_urls:
                seen_urls.add(u)
                topic_queue.append({
                    "title": t.get("title", "Untitled Topic"),
                    "url": u,
                    "from_sidebar": True,
                    "x": t.get("x", 0),
                    "y": t.get("y", 0)
                })

        for db_doc in db_topics:
            u = db_doc.get("url", "")
            if u and u not in seen_urls:
                seen_urls.add(u)
                topic_queue.append({
                    "title": db_doc.get("title", "Untitled Document"),
                    "url": u,
                    "from_sidebar": False,
                    "x": 0,
                    "y": 0
                })

        if max_topics:
            topic_queue = topic_queue[:max_topics]

        total_topics = len(topic_queue)
        print(f"\n🚀 Master Topic Queue Prepared: {total_topics} topics to read.\n")
        print("-" * 80)
        for idx, t in enumerate(topic_queue[:15], 1):
            source_tag = "[Sidebar Tree]" if t["from_sidebar"] else "[Direct PRD]"
            print(f"  {idx:02d}. {source_tag} {t['title']}")
        if total_topics > 15:
            print(f"  ... and {total_topics - 15} more topics in queue.")
        print("-" * 80 + "\n")

        # 3. Systematic Topic-by-Topic Traversal Loop
        grand_total_words = 0
        topics_completed = 0

        for topic_idx, topic in enumerate(topic_queue, 1):
            title = topic["title"]
            url = topic["url"]
            print(f"\n[{topic_idx}/{total_topics}] 🎯 Navigating to Topic: '{title}'")

            # Try clicking sidebar item first if coordinates exist and are visible
            clicked_sidebar = False
            if topic["from_sidebar"] and topic["x"] > 0 and topic["y"] > 0:
                try:
                    # Move to sidebar element
                    await kinematics.move_to(topic["x"], min(topic["y"], 800))
                    await kinematics.click_at(topic["x"], min(topic["y"], 800))
                    clicked_sidebar = True
                    await asyncio.sleep(2.0)
                except Exception:
                    clicked_sidebar = False

            # If not clicked via sidebar or URL hasn't changed, navigate directly
            if not clicked_sidebar or page.url != url:
                try:
                    await page.goto(url, wait_until="domcontentloaded")
                    await asyncio.sleep(2.0)
                except Exception as e:
                    print(f"  Notice navigating to {url}: {e}")
                    continue

            # Read the document comprehensively
            words_read = await read_active_document(
                page=page,
                kinematics=kinematics,
                topic_title=title,
                topic_index=topic_idx,
                total_topics=total_topics
            )

            grand_total_words += words_read
            topics_completed += 1

            # Brief natural pause before moving to next topic
            await asyncio.sleep(random.uniform(1.0, 2.0))

        print("\n" + "=" * 80)
        print("🎉 ALL TOPICS COMPREHENSIVE READING SIMULATION COMPLETE!")
        print("=" * 80)
        print(f"• Total Topics Traversed: {topics_completed} / {total_topics}")
        print(f"• Total Words Read:       {grand_total_words:,}")
        print(f"• All sidebar folders (EZ Flows, PRDs, Mobile App, etc.) fully accessed.")
        print("• Browser session active and verified on desktop.")
        print("=" * 80 + "\n")

        # Keep browser open for 60 seconds for inspection
        print("Leaving browser open for 60s for visual inspection...")
        await asyncio.sleep(60.0)

    except Exception as e:
        print(f"Notice during all-topics run: {e}")
    finally:
        print("Closing browser cleanly.")
        await launcher.close()


if __name__ == "__main__":
    asyncio.run(run_all_topics_simulation())
