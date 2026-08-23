"""
Visual Perception Engine
Extracts interactive element bounding boxes, injects Set-of-Marks (SOM) badges,
and builds accessibility (a11y) tree representations for Vision LLM reasoning.
"""

import base64
import json
import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("VisualPerception")

SOM_INJECTION_JS = """
(() => {
    // 1. Remove any previous SOM overlay tags
    document.querySelectorAll('.subagent-som-tag').forEach(el => el.remove());

    const interactableSelectors = [
        'button', 'a[href]', 'input', 'select', 'textarea',
        '[role="button"]', '[role="checkbox"]', '[role="radio"]',
        '[role="link"]', '[role="tab"]', '[role="menuitem"]',
        '[role="combobox"]', '[contenteditable="true"]'
    ];

    const elements = Array.from(document.querySelectorAll(interactableSelectors.join(',')))
        .filter(el => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width >= 6 && rect.height >= 6 &&
                   style.visibility !== 'hidden' &&
                   style.display !== 'none' &&
                   style.opacity !== '0' &&
                   rect.top >= -20 && rect.top <= window.innerHeight + 20 &&
                   rect.left >= -20 && rect.left <= window.innerWidth + 20;
        });

    const marks = [];

    elements.forEach((el, idx) => {
        const id = idx + 1;
        const rect = el.getBoundingClientRect();

        // Create visible numbered marker badge
        const badge = document.createElement('div');
        badge.className = 'subagent-som-tag';
        badge.innerText = `${id}`;
        badge.style.position = 'fixed';
        badge.style.top = `${Math.max(0, rect.top)}px`;
        badge.style.left = `${Math.max(0, rect.left)}px`;
        badge.style.backgroundColor = '#E60049';
        badge.style.color = '#FFFFFF';
        badge.style.fontSize = '11px';
        badge.style.fontFamily = 'monospace';
        badge.style.fontWeight = 'bold';
        badge.style.padding = '1px 4px';
        badge.style.borderRadius = '3px';
        badge.style.border = '1px solid #FFFFFF';
        badge.style.zIndex = '2147483647';
        badge.style.pointerEvents = 'none';
        badge.style.boxShadow = '0 1px 4px rgba(0,0,0,0.6)';
        document.body.appendChild(badge);

        // Extract semantic contextual metadata
        const label = el.getAttribute('aria-label') ||
                      el.getAttribute('placeholder') ||
                      el.getAttribute('title') ||
                      (el.labels && el.labels[0] ? el.labels[0].innerText : '') ||
                      el.innerText ||
                      el.value || '';

        marks.push({
            id: id,
            tag: el.tagName.toLowerCase(),
            type: el.getAttribute('type') || '',
            name: el.getAttribute('name') || '',
            id_attr: el.id || '',
            label: label.trim().replace(/\\s+/g, ' ').slice(0, 80),
            x: Math.round(rect.left + rect.width / 2),
            y: Math.round(rect.top + rect.height / 2),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        });
    });

    return marks;
})();
"""

SOM_CLEANUP_JS = """
(() => {
    document.querySelectorAll('.subagent-som-tag').forEach(el => el.remove());
})();
"""


class VisualPerceptionEngine:
    """Perception pipeline combining DOM inspection with Set-of-Marks visual coordinates."""

    def __init__(self, page: Any):
        self.page = page

    async def capture_state(self) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Injects SOM tags, captures full viewport screenshot (base64),
        and returns the interactive element map.
        """
        # Inject markers
        interactive_elements = await self.page.evaluate(SOM_INJECTION_JS)

        # Capture screenshot with visible markers
        screenshot_bytes = await self.page.screenshot(type="jpeg", quality=85)
        base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")

        # Clean up markers so page interaction remains authentic
        await self.page.evaluate(SOM_CLEANUP_JS)

        logger.info(f"Perception state captured: {len(interactive_elements)} interactable elements identified.")
        return base64_image, interactive_elements

    async def get_element_by_id(self, mark_id: int, elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Retrieves element coordinates and metadata by its Set-of-Marks ID."""
        for el in elements:
            if el["id"] == mark_id:
                return el
        return None
