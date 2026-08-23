"""
Human Kinematics & Interaction Dynamics (Enhanced)
Simulates biological human mouse trajectories via cubic Bézier curves,
stochastic typing cadences with Gaussian delays, momentum scrolling,
and physical screen coordinate geometry alignment to defeat Turnstile CDP checks.
"""

import math
import random
import asyncio
import logging
from typing import Tuple, List, Optional, Any, Dict

logger = logging.getLogger("HumanDynamics")


class HumanKinematics:
    """Human-like interaction dynamics defeating biometric and event-geometry bot checks."""

    def __init__(self, page: Any):
        self.page = page
        self.current_x = 200.0
        self.current_y = 200.0
        self.window_offsets: Dict[str, float] = {
            "screen_x": 0.0,
            "screen_y": 0.0,
            "toolbar_height": 85.0  # Browser tab bar & omnibox offset
        }

    async def sync_window_geometry(self):
        """Fetches browser window coordinates to compute realistic physical screen coordinates."""
        try:
            geom = await self.page.evaluate("""
                () => ({
                    screenX: window.screenX || 0,
                    screenY: window.screenY || 0,
                    outerWidth: window.outerWidth || 1920,
                    outerHeight: window.outerHeight || 1080,
                    innerWidth: window.innerWidth || 1920,
                    innerHeight: window.innerHeight || 1080
                })
            """)
            self.window_offsets["screen_x"] = float(geom.get("screenX", 0))
            self.window_offsets["screen_y"] = float(geom.get("screenY", 0))
            # Calculate physical toolbar/tab bar height
            diff_h = geom.get("outerHeight", 1080) - geom.get("innerHeight", 1080)
            self.window_offsets["toolbar_height"] = max(60.0, min(float(diff_h), 120.0))
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
        steps: int = 35
    ) -> List[Tuple[float, float]]:
        """Generates realistic human mouse trajectory with control point variation and jitter."""
        x0, y0 = start
        x3, y3 = end
        dx = x3 - x0
        dy = y3 - y0
        dist = math.hypot(dx, dy)

        # Deviation scaling based on distance
        deviation = min(max(dist * 0.25, 20.0), 120.0)

        # Control points with randomized perpendicular displacement
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
            # Apply ease-in ease-out smoothing
            t_smooth = t * t * (3.0 - 2.0 * t)
            x, y = self._calculate_bezier_point(t_smooth, (x0, y0), p1, p2, (x3, y3))

            # Add subtle physiological micro-jitter
            jitter_x = random.gauss(0, 0.35)
            jitter_y = random.gauss(0, 0.35)
            trajectory.append((x + jitter_x, y + jitter_y))

        return trajectory

    async def move_to(self, target_x: float, target_y: float, steps: Optional[int] = None):
        """Smoothly moves the mouse cursor to target coordinates along a Bézier curve."""
        if steps is None:
            dist = math.hypot(target_x - self.current_x, target_y - self.current_y)
            steps = max(15, min(int(dist / 12), 45))

        trajectory = self._generate_bezier_trajectory(
            (self.current_x, self.current_y),
            (target_x, target_y),
            steps=steps
        )

        for x, y in trajectory:
            await self.page.mouse.move(x, y)
            # Micro-sleep simulating 60-120Hz polling intervals
            await asyncio.sleep(random.uniform(0.006, 0.014))

        self.current_x = target_x
        self.current_y = target_y

    async def click_at(self, target_x: float, target_y: float, button: str = "left"):
        """Moves to coordinates and performs a human-timed mouse click."""
        await self.move_to(target_x, target_y)
        await asyncio.sleep(random.uniform(0.06, 0.14))
        await self.page.mouse.down(button=button)
        await asyncio.sleep(random.uniform(0.05, 0.11))
        await self.page.mouse.up(button=button)
        await asyncio.sleep(random.uniform(0.08, 0.18))

    async def human_type(
        self,
        text: str,
        wpm: int = 85,
        typo_rate: float = 0.015,
        target_selector: Optional[str] = None
    ):
        """
        Types text with biological cadence: Gaussian delay variance,
        word boundary pauses, and realistic typo-correction behavior.
        """
        if target_selector:
            box = await self.page.locator(target_selector).first.bounding_box()
            if box:
                await self.click_at(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            else:
                await self.page.locator(target_selector).first.focus()

        # Mean delay per character in seconds based on target WPM (avg 5 chars per word)
        mean_delay = 60.0 / (wpm * 5)
        std_dev = mean_delay * 0.35

        for i, char in enumerate(text):
            # 1. Simulate accidental typo and immediate correction
            if random.random() < typo_rate and char.isalpha():
                typo_char = chr(ord(char) + random.choice([-1, 1]))
                await self.page.keyboard.type(typo_char)
                await asyncio.sleep(random.uniform(0.12, 0.26))
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.08, 0.16))

            # 2. Type actual character
            await self.page.keyboard.type(char)

            # 3. Calculate dynamic pause interval
            delay = random.gauss(mean_delay, std_dev)
            delay = max(0.025, min(0.28, delay))

            # Extra pause on punctuation / word boundaries
            if char in " .!?,;\n":
                delay += random.uniform(0.12, 0.30)

            await asyncio.sleep(delay)

    async def human_scroll(self, scroll_delta_y: int, steps: int = 8):
        """Performs natural momentum scrolling with acceleration/deceleration physics."""
        step_delta = scroll_delta_y / steps
        for i in range(steps):
            factor = math.sin((i + 1) / steps * math.pi)
            actual_delta = step_delta * (0.6 + 0.8 * factor)
            await self.page.mouse.wheel(0, actual_delta)
            await asyncio.sleep(random.uniform(0.03, 0.07))
        await asyncio.sleep(random.uniform(0.15, 0.35))
