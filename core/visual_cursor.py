"""
Visual Cursor Overlay & Real-Time Tracking Animator
Injects a high-visibility, animated virtual human cursor onto the webpage
so the user can visually watch the simulated pointer glide across paragraphs,
draw click ripples, and highlight text in real time on their screen.
"""

CURSOR_OVERLAY_JS = """
(() => {
    if (document.getElementById('virtual-human-cursor')) return;

    // 1. Create virtual cursor element
    const cursor = document.createElement('div');
    cursor.id = 'virtual-human-cursor';
    cursor.style.position = 'fixed';
    cursor.style.width = '20px';
    cursor.style.height = '20px';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '2147483647';
    cursor.style.transition = 'transform 0.04s linear, opacity 0.2s';
    cursor.style.transform = 'translate(-50%, -50%)';

    // SVG Cursor icon with high-contrast red pointer & laser glow
    cursor.innerHTML = `
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" style="filter: drop-shadow(0 2px 5px rgba(0,0,0,0.6));">
            <path d="M4 2L22 13L13 15L9 24L4 2Z" fill="#FF0044" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/>
            <circle cx="5" cy="3" r="3" fill="#00FFFF" opacity="0.9"/>
        </svg>
    `;
    document.body.appendChild(cursor);

    // 2. Ripple click effect generator
    window.showClickRipple = (x, y) => {
        const ripple = document.createElement('div');
        ripple.style.position = 'fixed';
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        ripple.style.width = '10px';
        ripple.style.height = '10px';
        ripple.style.borderRadius = '50%';
        ripple.style.border = '3px solid #FF0055';
        ripple.style.backgroundColor = 'rgba(255, 0, 85, 0.3)';
        ripple.style.transform = 'translate(-50%, -50%) scale(1)';
        ripple.style.transition = 'transform 0.5s ease-out, opacity 0.5s ease-out';
        ripple.style.pointerEvents = 'none';
        ripple.style.zIndex = '2147483646';
        document.body.appendChild(ripple);

        requestAnimationFrame(() => {
            ripple.style.transform = 'translate(-50%, -50%) scale(5)';
            ripple.style.opacity = '0';
        });

        setTimeout(() => ripple.remove(), 600);
    };

    // 3. Move listener updating visual position
    window.updateVirtualCursor = (x, y) => {
        cursor.style.left = `${x}px`;
        cursor.style.top = `${y}px`;
    };
})();
"""

UPDATE_CURSOR_JS = """
(coords) => {
    if (window.updateVirtualCursor) {
        window.updateVirtualCursor(coords.x, coords.y);
    }
}
"""

SHOW_RIPPLE_JS = """
(coords) => {
    if (window.showClickRipple) {
        window.showClickRipple(coords.x, coords.y);
    }
}
"""
