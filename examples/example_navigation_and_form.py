"""
Example: Autonomous Navigation and Form Filling Workflow
Demonstrates using the Stealth Browsing Subagent to navigate, bypass anti-bot heuristics,
and fill out multi-field contact/lead forms with biological human dynamics.
"""

import os
import sys
import asyncio

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.subagent import AutonomousBrowsingSubagent


async def main():
    # Sample business payload
    lead_payload = {
        "full_name": "Alexander Vance",
        "email": "alexander.vance@soundmindlabs.com",
        "phone": "2244877847",
        "company": "SoundMind Systems",
        "job_title": "Director of Engineering",
        "website": "https://soundmindlabs.com",
        "message": "Inquiring about high-throughput enterprise automation pipelines and stealth integration."
    }

    # Initialize subagent (Headless=False for local visual inspection)
    subagent = AutonomousBrowsingSubagent(headless=True)

    try:
        await subagent.start()

        # Target test endpoint (Example: HTTPBin form or any target contact form)
        target_url = "https://httpbin.org/forms/post"
        output_screenshot = os.path.abspath("form_verification.png")

        print(f"\n[1/3] Navigating to {target_url}...")
        result = await subagent.navigate_and_fill(
            url=target_url,
            form_data=lead_payload,
            auto_submit=False,
            screenshot_path=output_screenshot
        )

        print("\n[2/3] Execution Summary:")
        print(f"  • Page Title: {result['title']}")
        print(f"  • Interactive Elements Discovered: {result['elements_detected']}")
        print(f"  • Fields Matched & Filled: {result['fill_results']['total_fields_matched']}")
        for k, v in result['fill_results']['filled_fields'].items():
            print(f"      - {k}: '{v}'")

        print(f"\n[3/3] Screenshot saved to: {output_screenshot}")

    finally:
        await subagent.stop()


if __name__ == "__main__":
    asyncio.run(main())
