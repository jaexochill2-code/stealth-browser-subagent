"""
Atlassian Cloud REST API Client
Provides high-speed extraction of Confluence spaces/pages and Jira issues/projects
using Atlassian API tokens.
"""

import base64
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.parse
import json

logger = logging.getLogger("AtlassianAPI")


class AtlassianAPIClient:
    """Client for Jira Cloud REST API v3 and Confluence Cloud REST API v2."""

    def __init__(self, domain: str, email: str, api_token: str):
        # Normalize domain
        domain = domain.strip().rstrip("/")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        if not domain.endswith(".atlassian.net") and "atlassian.net" not in domain:
            domain = f"{domain}.atlassian.net"

        self.domain = domain
        self.email = email
        self.api_token = api_token
        auth_bytes = f"{email}:{api_token}".encode("utf-8")
        self.auth_header = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes an authenticated GET request against the Atlassian Cloud site."""
        url = f"{self.domain}{path}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(url, headers={
            "Authorization": self.auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AtlassianSubagent/1.0"
        })

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"Atlassian API Error ({e.code}) on {url}: {err_body}")
            raise RuntimeError(f"Atlassian API HTTP {e.code}: {err_body}")

    def verify_credentials(self) -> Dict[str, Any]:
        """Verifies authentication and returns current user metadata."""
        # Try Jira myself endpoint
        try:
            user_data = self._request("/rest/api/3/myself")
            logger.info(f"Connected to Jira as: {user_data.get('displayName')} ({user_data.get('emailAddress')})")
            return {"type": "jira", "user": user_data}
        except Exception:
            # Fallback to Confluence current user
            user_data = self._request("/wiki/rest/api/user/current")
            logger.info(f"Connected to Confluence as: {user_data.get('displayName')}")
            return {"type": "confluence", "user": user_data}

    def get_confluence_spaces(self) -> List[Dict[str, Any]]:
        """Retrieves all Confluence spaces accessible to the user."""
        res = self._request("/wiki/api/v2/spaces")
        return res.get("results", [])

    def get_confluence_pages(self, space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves Confluence pages accessible to the user (including shared documents)."""
        params = {"limit": 50}
        if space_id:
            params["space-id"] = space_id
        res = self._request("/wiki/api/v2/pages", params=params)
        return res.get("results", [])

    def get_confluence_page_content(self, page_id: str) -> Dict[str, Any]:
        """Retrieves full content body (storage format / markdown) of a specific Confluence page."""
        params = {"body-format": "storage"}
        return self._request(f"/wiki/api/v2/pages/{page_id}", params=params)

    def get_jira_projects(self) -> List[Dict[str, Any]]:
        """Retrieves all Jira projects accessible to the user."""
        return self._request("/rest/api/3/project")

    def search_jira_issues(self, jql: str = "order by created DESC", limit: int = 50) -> List[Dict[str, Any]]:
        """Searches Jira issues using JQL."""
        params = {"jql": jql, "maxResults": limit}
        res = self._request("/rest/api/3/search", params=params)
        return res.get("issues", [])
