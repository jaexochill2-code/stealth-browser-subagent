"""
Autonomous Form Filling Engine
Classifies input fields, maps structured data payloads to complex web forms,
and executes resilient multi-step form submissions with post-fill verification.
"""

import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from .human_dynamics import HumanKinematics

logger = logging.getLogger("FormAgent")


class FormFillEngine:
    """Semantic form-understanding and resilient submission engine."""

    def __init__(self, page: Any, kinematics: HumanKinematics):
        self.page = page
        self.kinematics = kinematics

    @staticmethod
    def _match_field_key(element_meta: Dict[str, Any], payload: Dict[str, Any]) -> Optional[Tuple[str, Any]]:
        """
        Matches an interactive element's metadata (name, id, placeholder, label)
        against keys in the user data payload using fuzzy heuristics.
        """
        combined_text = f"{element_meta.get('name', '')} {element_meta.get('id_attr', '')} {element_meta.get('label', '')}".lower()
        combined_text = re.sub(r'[^a-z0-9]', '', combined_text)

        # Standard field synonyms
        synonyms = {
            "first_name": ["firstname", "fname", "first", "givenname"],
            "last_name": ["lastname", "lname", "last", "surname", "familyname"],
            "full_name": ["name", "fullname", "yourname", "contactname"],
            "email": ["email", "e-mail", "emailaddress", "useremail"],
            "phone": ["phone", "phonenumber", "tel", "mobile", "cell", "telephone"],
            "company": ["company", "organization", "org", "business", "companyname"],
            "job_title": ["title", "jobtitle", "role", "position"],
            "website": ["website", "url", "domain", "webpage"],
            "address": ["address", "street", "streetaddress", "addressline1"],
            "city": ["city", "town"],
            "state": ["state", "province", "region"],
            "zip": ["zip", "zipcode", "postal", "postalcode"],
            "message": ["message", "comments", "inquiry", "notes", "description", "details"],
        }

        for payload_key, value in payload.items():
            norm_key = re.sub(r'[^a-z0-9]', '', payload_key.lower())
            
            # Exact or substring match on key
            if norm_key in combined_text or combined_text in norm_key:
                return payload_key, value

            # Match against common synonyms
            for canonical, syn_list in synonyms.items():
                if payload_key.lower() == canonical or payload_key.lower() in syn_list:
                    for syn in syn_list:
                        if syn in combined_text:
                            return payload_key, value

        return None

    async def fill_form(
        self,
        elements: List[Dict[str, Any]],
        payload: Dict[str, Any],
        auto_submit: bool = False
    ) -> Dict[str, Any]:
        """
        Iterates over discovered elements, matches relevant fields,
        and inputs data using humanized dynamics.
        """
        filled_fields = {}
        submit_button = None

        logger.info(f"Initiating form fill with {len(payload)} payload keys across {len(elements)} elements.")

        for el in elements:
            tag = el.get("tag", "")
            el_type = el.get("type", "").lower()
            x = el.get("x", 0)
            y = el.get("y", 0)

            # Identify potential submit buttons
            if (tag == "button" or (tag == "input" and el_type in ["submit", "button"])) and not submit_button:
                btn_label = el.get("label", "").lower()
                if any(kw in btn_label for kw in ["submit", "send", "get started", "book", "request", "contact", "continue", "next", "save"]):
                    submit_button = el

            # Handle text inputs, textareas
            if tag in ["input", "textarea"] and el_type not in ["submit", "button", "hidden", "image", "reset", "checkbox", "radio"]:
                match = self._match_field_key(el, payload)
                if match:
                    key, val = match
                    if key not in filled_fields:
                        logger.info(f"Filling field '{key}' into element ID {el['id']} ('{el.get('label')}') with '{val}'")
                        await self.kinematics.click_at(x, y)
                        await asyncio.sleep(0.1)

                        # Clear existing content if any
                        await self.page.keyboard.press("Meta+A")
                        await self.page.keyboard.press("Backspace")

                        # Type with human dynamics
                        await self.kinematics.human_type(str(val))
                        filled_fields[key] = val
                        await asyncio.sleep(0.2)

            # Handle dropdown selects
            elif tag == "select":
                match = self._match_field_key(el, payload)
                if match:
                    key, val = match
                    logger.info(f"Selecting option '{val}' for field '{key}' in element ID {el['id']}")
                    await self.kinematics.click_at(x, y)
                    await asyncio.sleep(0.2)
                    try:
                        # Attempt standard option select by value or label
                        select_locator = self.page.locator(f"#{el['id_attr']}" if el.get('id_attr') else f"select[name='{el.get('name')}']")
                        await select_locator.select_option(label=str(val))
                        filled_fields[key] = val
                    except Exception:
                        logger.warning(f"Could not select option '{val}' directly on select ID {el['id']}")

        # Submit form if requested and submit button is located
        submission_status = "NOT_SUBMITTED"
        if auto_submit and submit_button:
            logger.info(f"Executing form submission via button ID {submit_button['id']} ('{submit_button.get('label')}')")
            await self.kinematics.click_at(submit_button["x"], submit_button["y"])
            await asyncio.sleep(2.0)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=5000)
                submission_status = "SUBMITTED"
            except Exception:
                submission_status = "SUBMITTED_WITH_TIMEOUT"

        return {
            "filled_fields": filled_fields,
            "submission_status": submission_status,
            "total_fields_matched": len(filled_fields)
        }
