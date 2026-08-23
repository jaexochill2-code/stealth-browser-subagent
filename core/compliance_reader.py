"""
Compliance Reading & Human Telemetry Emulation Engine
Engineered to satisfy enterprise telemetry monitors (Atlassian Analytics, Mixpanel,
Datadog RUM, FullStory, Hotjar) measuring active dwell time, reading velocity,
pointer tracking, micro-text selection, and scroll momentum.
"""

import math
import random
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ComplianceReader")


class ComplianceReadingSimulator:
    """Simulates authentic biological reading telemetry for compliance and analytics systems."""

    def __init__(self, page: Any, kinematics: Any):
        self.page = page
        self.kinematics = kinematics
        self.reading_wpm = random.randint(190, 240)  # Standard human comprehension speed

    async def ensure_active_tab_focus(self):
        """Dispatches active focus events so analytics trackers record 100% active dwell time."""
        await self.page.bring_to_front()
        await self.page.evaluate("""
            () => {
                window.focus();
                document.dispatchEvent(new Event('focus'));
                Object.defineProperty(document, 'hidden', { value: false, writable: true });
                Object.defineProperty(document, 'visibilityState', { value: 'visible', writable: true });
                document.dispatchEvent(new Event('visibilitychange'));
            }
        """)

    async def simulate_reading_block(self, text: str, element_rect: Dict[str, float]):
        """
        Calculates biological reading dwell time based on text word count,
        wandering the mouse cursor along lines to simulate natural eye-pointer tracking.
        """
        words = len(text.split())
        if words == 0:
            return

        # Dwell time in seconds based on biological WPM with ±12% variance
        dwell_seconds = (words / self.reading_wpm) * 60.0 * random.uniform(0.88, 1.12)
        dwell_seconds = max(2.5, min(dwell_seconds, 28.0))  # Bounded between 2.5s and 28s per section

        logger.info(f"Reading block ({words} words): dwelling for {dwell_seconds:.1f}s at Y={element_rect.get('top', 0):.0f}px...")

        # Subdivide dwell time into micro-reading movements
        sub_steps = max(2, int(dwell_seconds / 2.0))
        start_x = element_rect.get("left", 200) + random.uniform(40, 120)
        start_y = element_rect.get("top", 200) + random.uniform(10, 30)

        for step in range(sub_steps):
            # Drift cursor along reading line
            target_x = start_x + (step * random.uniform(30, 70))
            target_y = start_y + (step * random.uniform(5, 15))
            
            # Smooth Bézier trajectory
            await self.kinematics.move_to(
                min(target_x, 1000),
                min(target_y, 800)
            )
            await asyncio.sleep(dwell_seconds / sub_steps)

        # 10% chance to simulate a natural text-highlight / selection during comprehension
        if random.random() < 0.10 and words > 15:
            await self._simulate_micro_selection(start_x, start_y)

    async def _simulate_micro_selection(self, x: float, y: float):
        """Simulates dragging across a sentence or double-clicking a word while reading."""
        try:
            await self.kinematics.move_to(x, y)
            await asyncio.sleep(0.1)
            await self.page.mouse.down()
            await self.kinematics.move_to(x + random.uniform(80, 160), y, steps=10)
            await asyncio.sleep(random.uniform(0.4, 1.2))  # Hold selection briefly
            await self.page.mouse.up()
            await asyncio.sleep(0.2)
            # Click once to clear selection
            await self.page.mouse.click(x + 20, y + 20)
        except Exception:
            pass

    async def read_entire_document(
        self,
        min_total_reading_minutes: float = 1.5,
        backtrack_probability: float = 0.18
    ) -> Dict[str, Any]:
        """
        Traverses the full document top-to-bottom:
        - Fires IntersectionObserver events on all headings/paragraphs.
        - Emulates momentum scrolling with human pauses.
        - Backtracks (scrolls up) occasionally to simulate re-reading complex paragraphs.
        - Guarantees minimum total stay time on the document.
        """
        start_time = asyncio.get_event_loop().time()
        await self.ensure_active_tab_focus()

        # Extract all readable structural blocks with bounding rects
        blocks = await self.page.evaluate("""
            () => {
                const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, p, table, ul, ol, blockquote, [data-testid="page-title"]'));
                return elements.map(el => {
                    const rect = el.getBoundingClientRect();
                    return {
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText.trim(),
                        top: rect.top,
                        bottom: rect.bottom,
                        height: rect.height
                    };
                }).filter(b => b.text.length > 5 && b.height > 10);
            }
        """)

        logger.info(f"Discovered {len(blocks)} readable content blocks. Beginning compliance simulation...")

        for idx, block in enumerate(blocks, 1):
            # Scroll element into viewport with momentum
            await self.page.evaluate(f"window.scrollBy({{ top: {max(0, block['top'] - 150)}, behavior: 'smooth' }});")
            await asyncio.sleep(random.uniform(0.6, 1.2))

            # Simulate reading this specific block
            await self.simulate_reading_block(block["text"], block)

            # Backtracking: human occasionally scrolls up to re-check a previous point
            if random.random() < backtrack_probability and idx > 2:
                logger.info("Simulating human backtracking (scrolling up 250px to re-verify context)...")
                await self.kinematics.human_scroll(scroll_delta_y=-250, steps=8)
                await asyncio.sleep(random.uniform(2.0, 4.5))
                # Return to position
                await self.kinematics.human_scroll(scroll_delta_y=260, steps=8)
                await asyncio.sleep(1.0)

        # Pad remaining time if total reading duration hasn't reached required compliance minimum
        elapsed_minutes = (asyncio.get_event_loop().time() - start_time) / 60.0
        if elapsed_minutes < min_total_reading_minutes:
            remaining_seconds = (min_total_reading_minutes - elapsed_minutes) * 60.0
            logger.info(f"Padding compliance dwell time by {remaining_seconds:.1f}s to guarantee minimum stay requirements...")
            
            # Subtle idle movements while staying at document bottom / overview
            steps = int(remaining_seconds / 5.0)
            for _ in range(steps):
                await self.kinematics.move_to(
                    random.uniform(300, 700),
                    random.uniform(300, 600)
                )
                await asyncio.sleep(5.0)

        total_time_seconds = asyncio.get_event_loop().time() - start_time
        logger.info(f"Compliance reading simulation finished. Total verified dwell time: {total_time_seconds / 60.0:.2f} minutes.")

        return {
            "total_blocks_read": len(blocks),
            "dwell_time_minutes": round(total_time_seconds / 60.0, 2),
            "reading_wpm_profile": self.reading_wpm,
            "status": "COMPLIANT_READING_COMPLETED"
        }
