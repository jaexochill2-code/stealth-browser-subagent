"""
Universal CLI Runner for Stealth Browser & Atlassian Compliance Workflows
Usage:
  python3 run.py --visual                  # Run visible on-screen laser cursor reading
  python3 run.py --url "https://..."       # Run compliance reading on any specific URL
  python3 run.py --rag "search query"      # Query the local Confluence RAG database
  python3 run.py --sync-rag                # Re-sync all Confluence documents into RAG DB
"""

import sys
import os
import argparse
import asyncio
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Stealth Browser & Compliance Reader Suite")
    parser.add_argument("--visual", action="store_true", help="Launch visible desktop Chrome with neon laser pointer")
    parser.add_argument("--url", type=str, default=None, help="Target document URL to read")
    parser.add_argument("--minutes", type=float, default=2.0, help="Minimum compliance dwell time in minutes (default: 2.0)")
    parser.add_argument("--rag", type=str, default=None, help="Search the local Confluence RAG knowledge base")
    parser.add_argument("--sync-rag", action="store_true", help="Fetch latest Confluence pages and rebuild RAG database")

    args = parser.parse_args()

    default_url = "https://ezai.atlassian.net/wiki/spaces/~712020c417f00f557b4609b0d12ac7aa79e5d8/pages/196706/Getting+started+in+Confluence+from+Jira"
    target_url = args.url or default_url

    # 1. Query RAG Database
    if args.rag:
        from core.rag_engine import ConfluenceRAGDatabase
        db = ConfluenceRAGDatabase("knowledge_rag.db")
        print(f"\n🔍 Searching RAG Knowledge Base for: '{args.rag}'\n" + "=" * 60)
        results = db.search_rag(args.rag, limit=4)
        if not results:
            print("No matching document chunks found.")
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['title']} > {r['section_title']} (Score: {r['score']:.4f})")
            print(f"    URL: {r['url']}")
            print(f"    Preview: {r['content'][:250]}...\n")
        return

    # 2. Sync RAG Database
    if args.sync_rag:
        print("🔄 Re-syncing Confluence documents into local RAG database...")
        import build_rag_database
        build_rag_database.main()
        return

    # 3. Visual Interactive Deep Reader
    if args.visual:
        import examples.full_deep_reading_simulation as deep_reader
        asyncio.run(deep_reader.run_full_deep_simulation(
            target_url=target_url,
            keep_alive_minutes=int(args.minutes or 20)
        ))
        return

    # 4. Background Compliance Reading
    from examples.run_compliance_reading import execute_compliance_read
    print(f"🚀 Starting compliance reading on:\n   {target_url}\n   Min Dwell Time: {args.minutes} mins")
    asyncio.run(execute_compliance_read(target_url=target_url, min_reading_minutes=args.minutes, headless=True))


if __name__ == "__main__":
    main()
