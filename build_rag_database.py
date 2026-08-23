"""
RAG Ingestion Pipeline
Fetches all accessible Confluence documents from ezai.atlassian.net and local cache,
converts them into semantic chunks, and builds the knowledge_rag.db SQLite database.
"""

import os
import json
import base64
import urllib.request
import urllib.parse
from core.rag_engine import ConfluenceRAGDatabase


def load_vault_credentials():
    config_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
            vault = cfg.get("_vault", {})
            return (
                os.environ.get("ATLASSIAN_DOMAIN", "https://ezai.atlassian.net"),
                os.environ.get("ATLASSIAN_EMAIL", "support@ezebld.ai"),
                os.environ.get("ATLASSIAN_API_TOKEN", vault.get("atlassian_api_token", ""))
            )
    return (
        os.environ.get("ATLASSIAN_DOMAIN", "https://ezai.atlassian.net"),
        os.environ.get("ATLASSIAN_EMAIL", "support@ezebld.ai"),
        os.environ.get("ATLASSIAN_API_TOKEN", "")
    )


def main():
    domain, email, api_token = load_vault_credentials()
    if not api_token:
        raise ValueError("Atlassian API token not found in _vault or environment.")

    auth_bytes = f"{email}:{api_token}".encode("utf-8")
    auth_header = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"

    def fetch_api(url):
        req = urllib.request.Request(url, headers={
            "Authorization": auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "RAGIngestion/1.0"
        })
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"Notice during fetch of {url}: {e}")
            return None

    db_path = "/Users/flowstatework/.gemini/antigravity-ide/scratch/stealth-browser-subagent/knowledge_rag.db"
    rag_db = ConfluenceRAGDatabase(db_path=db_path)

    # 1. Fetch all spaces map
    spaces_data = fetch_api(f"{domain}/wiki/api/v2/spaces")
    spaces_map = {}
    if spaces_data and "results" in spaces_data:
        for sp in spaces_data["results"]:
            spaces_map[sp["id"]] = sp["name"]

    print(f"Loaded {len(spaces_map)} spaces from Confluence.")

    # 2. Fetch pages with full body storage format
    page_url = f"{domain}/wiki/api/v2/pages?limit=100&body-format=storage"
    total_indexed = 0

    while page_url:
        data = fetch_api(page_url)
        if not data or "results" not in data:
            break

        results = data["results"]
        for p in results:
            page_id = p.get("id")
            title = p.get("title", "Untitled")
            space_id = p.get("spaceId", "")
            space_name = spaces_map.get(space_id, "General")
            created_at = p.get("createdAt", "")
            raw_html = p.get("body", {}).get("storage", {}).get("value", "")
            page_web_url = f"{domain}/wiki/spaces/{space_id}/pages/{page_id}"

            if raw_html:
                rag_db.insert_document(
                    page_id=page_id,
                    title=title,
                    raw_html=raw_html,
                    space_id=space_id,
                    space_name=space_name,
                    url=page_web_url,
                    created_at=created_at
                )
                total_indexed += 1

        # Check next page cursor
        links = data.get("_links", {})
        next_link = links.get("next")
        if next_link:
            page_url = f"{domain}/wiki{next_link}" if not next_link.startswith("http") else next_link
        else:
            page_url = None

    # Index explicit key PRD targets
    for pid in ["145031172", "196706"]:
        data = fetch_api(f"{domain}/wiki/api/v2/pages/{pid}?body-format=storage")
        if data:
            rag_db.insert_document(
                page_id=pid,
                title=data.get("title", ""),
                raw_html=data.get("body", {}).get("storage", {}).get("value", ""),
                space_id=data.get("spaceId", ""),
                space_name="Netanel Gabizon",
                url=f"{domain}/wiki/spaces/{data.get('spaceId')}/pages/{pid}",
                created_at=data.get("createdAt", "")
            )

    stats = rag_db.get_stats()
    print("\n=== RAG DATABASE BUILD COMPLETE ===")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Chunks:    {stats['total_chunks']}")
    print(f"Total Spaces:    {stats['total_spaces']}")
    print(f"Database Size:   {stats['db_size_kb']} KB")
    print(f"Database Path:   {stats['db_path']}")


if __name__ == "__main__":
    main()
