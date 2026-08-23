# Stealth Browser Subagent (2026 Edition)

An enterprise-grade, autonomous web browsing, perception, and form-filling subagent built for modern WAF environments (Cloudflare Turnstile, DataDome, Akamai, Kasada).

---

## Key Features

1. **Anti-Bot & CDP Hardening**:
   - Built on `rebrowser-playwright` / `DrissionPage` to eliminate `Runtime.enable` and WebDriver detection leaks.
   - Randomized viewport, hardware flags, and Chrome runtime mocks.
2. **Biological Biometrics & Human Dynamics**:
   - **Bézier Mouse Trajectories**: 3rd-order Bézier curves with dynamic control point calculation and physiological micro-jitter.
   - **Stochastic Typing**: Gaussian-distributed keystroke flight times (60–110 WPM), natural word-boundary pauses, and simulated typo/backspace corrections.
   - **Momentum Scrolling**: Sine-decay acceleration/deceleration physics.
3. **Visual Perception & Grounding**:
   - **Set-of-Marks (SOM)**: Numbered bounding box badges injected into the viewport for 100% accurate coordinate targeting by Vision LLMs (Gemini 3.5/3.7 Flash).
   - **Accessibility Tree Extraction**: Semantic parsing of labels, ARIA attributes, and element hierarchies.
4. **WAF & Shadow DOM Resolution**:
   - Automated detection of Cloudflare Turnstile iframes and DataDome challenges.
   - Multi-layer shadow root recursion to click verification checkboxes.
5. **Autonomous Form Intelligence**:
   - Fuzzy synonym matching for common lead/contact form schemas.
   - Multi-type element handling (text inputs, selects, radio groups, textareas).

---

## Directory Structure

```
stealth-browser-subagent/
├── core/
│   ├── stealth_browser.py     # Hardened browser launch & context isolation
│   ├── human_dynamics.py      # Bézier curves, jitter, humanized typing
│   ├── perception.py          # SOM visual injection & a11y DOM parser
│   ├── waf_solver.py          # Turnstile & closed shadow DOM solver
│   └── form_agent.py          # Form understanding & fill pipeline
├── agents/
│   └── subagent.py            # Orchestrator with Gemini Multimodal reasoning
├── examples/
│   └── example_navigation_and_form.py # Working end-to-end demo
├── docs/
│   ├── RESEARCH_COMPENDIUM.md # Full 2026 research documentation
│   └── ARCHITECTURE.md        # Technical architecture specification
├── requirements.txt
└── README.md
```

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Run Example Navigation & Form Filling
```bash
python examples/example_navigation_and_form.py
```

### 3. Using in Your Own Code
```python
import asyncio
from agents.subagent import AutonomousBrowsingSubagent

async def main():
    agent = AutonomousBrowsingSubagent(headless=False)
    await agent.start()

    payload = {
        "full_name": "Alexander Vance",
        "email": "alexander.vance@soundmindlabs.com",
        "phone": "2244877847",
        "company": "SoundMind Systems",
        "message": "Inquiry regarding enterprise automation pipelines."
    }

    result = await agent.navigate_and_fill(
        url="https://example.com/contact",
        form_data=payload,
        auto_submit=False,
        screenshot_path="verification.png"
    )

    print("Result:", result)
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Documentation Links

- Detailed WAF & Anti-Bot Detection Matrix: [`docs/RESEARCH_COMPENDIUM.md`](docs/RESEARCH_COMPENDIUM.md)
- Subagent Architecture & Design Spec: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
