"""
Human Kinematics & Interaction Dynamics (Visible Cursor Edition)
Simulates biological human mouse trajectories via cubic Bézier curves,
stochastic typing cadences with Gaussian delays, momentum scrolling,
and real-time visual cursor overlay rendering.
"""

import math
import random
import asyncio
import logging
from typing import Tuple, List, Optional, Any, Dict
from .visual_cursor import CURSOR_OVERLAY_JS, UPDATE_CURSOR_JS, SHOW_RIPPLE_JS

logger = logging.getLogger("HumanDynamics")


class HumanKinematics:
    """Human-like interaction dynamics with visible on-screen cursor tracking."""

    def __init__(self, page: Any):
        self.page = page
        self.current_x = 200.0
        self.current_y = 200.0
        self.cursor_injected = False
        self.window_offsets: Dict[str, float] = {
            "screen_x": 0.0,
            "screen_y": 0.0,
            "toolbar_height": 85.0
        }

    async def inject_visual_cursor(self):
        """Injects a bright visible virtual cursor overlay into the page."""
        try:
            await self.page.evaluate(CURSOR_OVERLAY_JS)
            self.cursor_injected = True
        except Exception:
            pass

    async def sync_window_geometry(self):
        """Fetches browser window coordinates to compute realistic physical screen coordinates."""
        try:
            geom = await self.page.evaluate("""
                () => ({
                    screenX: window.screenX || 0,
                    screenY: window.screenY || 0,
                    outerWidth: window.outerWidth || 1400,
                    outerHeight: window.outerHeight || 900,
                    innerWidth: window.innerWidth || 1400,
                    innerHeight: window.innerHeight || 900
                })
            """)
            self.window_offsets["screen_x"] = float(geom.get("screenX", 0))
            self.window_offsets["screen_y"] = float(geom.get("screenY", 0))
            diff_h = geom.get("outerHeight", 900) - geom.get("innerHeight", 900)
            self.window_offsets["toolbar_height"] = max(60.0, min(float(diff_h), 120.0))
            await self.inject_visual_cursor()
        except Exception:
            pass

    @staticmethod
    def _calculate_bezier_point(
        t: float,
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Calculates a point on a cubic Bézier curve at parameter t in [0, 1]."""
        u = 1.0 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t

        x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
        y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
        return x, y

    def _generate_bezier_trajectory(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        steps: int = 30
    ) -> List[Tuple[float, float]]:
        """Generates realistic human mouse trajectory with control point variation and jitter."""
        x0, y0 = start
        x3, y3 = end
        dx = x3 - x0
        dy = y3 - y0
        dist = math.hypot(dx, dy)

        deviation = min(max(dist * 0.25, 20.0), 100.0)

        p1 = (
            x0 + dx * random.uniform(0.15, 0.45) + random.uniform(-deviation, deviation),
            y0 + dy * random.uniform(0.15, 0.45) + random.uniform(-deviation, deviation)
        )
        p2 = (
            x0 + dx * random.uniform(0.55, 0.85) + random.uniform(-deviation * 0.7, deviation * 0.7),
            y0 + dy * random.uniform(0.55, 0.85) + random.uniform(-deviation * 0.7, deviation * 0.7)
        )

        trajectory = []
        for i in range(steps + 1):
            t = i / steps
            t_smooth = t * t * (3.0 - 2.0 * t)
            x, y = self._calculate_bezier_point(t_smooth, (x0, y0), p1, p2, (x3, y3))
            jitter_x = random.gauss(0, 0.3)
            jitter_y = random.gauss(0, 0.3)
            trajectory.append((x + jitter_x, y + jitter_y))

        return trajectory

    async def move_to(self, target_x: float, target_y: float, steps: Optional[int] = None):
        """Smoothly moves the mouse cursor and updates the visible cursor overlay."""
        if steps is None:
            dist = math.hypot(target_x - self.current_x, target_y - self.current_y)
            steps = max(15, min(int(dist / 14), 40))

        trajectory = self._generate_bezier_trajectory(
            (self.current_x, self.current_y),
            (target_x, target_y),
            steps=steps
        )

        for x, y in trajectory:
            await self.page.mouse.move(x, y)
            # Update visual overlay
            try:
                await self.page.evaluate(UPDATE_CURSOR_JS, {"x": round(x), "y": round(y)})
            except Exception:
                pass
            await asyncio.sleep(random.uniform(0.010, 0.022))

        self.current_x = target_x
        self.current_y = target_y

    async def click_at(self, target_x: float, target_y: float, button: str = "left"):
        """Moves to coordinates, animates a visual ripple, and performs a human-timed mouse click."""
        await self.move_to(target_x, target_y)
        await asyncio.sleep(random.uniform(0.08, 0.16))
        
        # Animate visual ripple
        try:
            await self.page.evaluate(SHOW_RIPPLE_JS, {"x": round(target_x), "y": round(target_y)})
        except Exception:
            pass

        await self.page.mouse.down(button=button)
        await asyncio.sleep(random.uniform(0.06, 0.12))
        await self.page.mouse.up(button=button)
        await asyncio.sleep(random.uniform(0.10, 0.20))

    async def human_type(
        self,
        text: str,
        wpm: int = 80,
        typo_rate: float = 0.015,
        target_selector: Optional[str] = None
    ):
        """Types text with biological cadence and natural pauses."""
        if target_selector:
            box = await self.page.locator(target_selector).first.bounding_box()
            if box:
                await self.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            else:
                await self.page.locator(target_selector).first.focus()

        mean_delay = 60.0 / (wpm * 5)
        std_dev = mean_delay * 0.35

        for char in text:
            if random.random() < typo_rate and char.isalpha():
                typo_char = chr(ord(char) + random.choice([-1, 1]))
                await self.page.keyboard.type(typo_char)
                await asyncio.sleep(random.uniform(0.12, 0.26))
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.08, 0.16))

            await self.page.keyboard.type(char)
            delay = max(0.03, min(0.28, random.gauss(mean_delay, std_dev)))
            if char in " .!?,;\n":
                delay += random.uniform(0.15, 0.35)
            await asyncio.sleep(delay)

    async def human_scroll(self, scroll_delta_y: int, steps: int = 12):
        """Performs natural momentum scrolling with acceleration/deceleration physics."""
        step_delta = scroll_delta_y / steps
        for i in range(steps):
            factor = math.sin((i + 1) / steps * math.pi)
            actual_delta = step_delta * (0.6 + 0.8 * factor)
            await self.page.mouse.wheel(0, actual_delta)
            await asyncio.sleep(random.uniform(0.04, 0.09))
        await asyncio.sleep(random.uniform(0.2, 0.5))
