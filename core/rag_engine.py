"""
RAG Knowledge Database & Semantic Indexing Engine
Builds and manages a SQLite-backed structured knowledge database with FTS5 full-text search,
semantic chunking, metadata tagging, and knowledge graph relations for Confluence/PRD documentation.
"""

import os
import re
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("RAGEngine")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")


class ConfluenceRAGDatabase:
    """Production SQLite knowledge database for Confluence PRDs and technical documentation."""

    def __init__(self, db_path: str = "knowledge_rag.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes database schema with FTS5 full-text search and knowledge graph tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    space_id TEXT,
                    space_name TEXT,
                    page_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    url TEXT,
                    created_at TEXT,
                    char_count INTEGER,
                    word_count INTEGER,
                    raw_html TEXT,
                    clean_markdown TEXT
                )
            """)

            # 2. Document chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    section_title TEXT,
                    content TEXT NOT NULL,
                    token_estimate INTEGER,
                    keywords_json TEXT,
                    metadata_json TEXT,
                    FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                )
            """)

            # 3. FTS5 Full-Text Search Virtual Table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                    chunk_id UNINDEXED,
                    doc_id UNINDEXED,
                    title,
                    section_title,
                    content,
                    tokenize = 'porter unicode61'
                )
            """)

            # 4. Knowledge Graph Entities
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kg_entities (
                    entity_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    entity_type TEXT NOT NULL,
                    description TEXT,
                    metadata_json TEXT
                )
            """)

            # 5. Knowledge Graph Relations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kg_relations (
                    relation_id TEXT PRIMARY KEY,
                    source_entity TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    target_entity TEXT NOT NULL,
                    doc_id TEXT,
                    metadata_json TEXT
                )
            """)

            conn.commit()
            logger.info(f"RAG Database initialized at: {self.db_path}")

    @staticmethod
    def html_to_clean_markdown(html_content: str) -> str:
        """Converts raw Confluence HTML / storage format to clean Markdown."""
        text = html_content
        # Remove XML tags and macros
        text = re.sub(r'<ac:[^>]+>', '', text)
        text = re.sub(r'</ac:[^>]+>', '', text)
        text = re.sub(r'<ri:[^>]+>', '', text)
        
        # Headers
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
        text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL)
        
        # Lists
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'\n* \1', text, flags=re.DOTALL)
        text = re.sub(r'</?(ul|ol)[^>]*>', '\n', text)
        
        # Paragraphs & line breaks
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', text, flags=re.DOTALL)
        
        # Strip all remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def chunk_document(self, title: str, markdown: str, max_chunk_words: int = 250) -> List[Dict[str, Any]]:
        """Splits markdown content into semantic chunks bounded by headers and paragraphs."""
        sections = re.split(r'\n(?=#{1,4}\s)', markdown)
        chunks = []
        chunk_idx = 0

        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            # Extract section title
            first_line = sec.split('\n')[0]
            section_title = first_line.lstrip('#').strip() if first_line.startswith('#') else title

            words = sec.split()
            if len(words) <= max_chunk_words:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "section_title": section_title,
                    "content": sec,
                    "token_estimate": int(len(words) * 1.3),
                    "keywords": list(set(re.findall(r'\b[A-Za-z]{4,}\b', sec.lower())))[:12]
                })
                chunk_idx += 1
            else:
                # Sub-chunk by paragraphs
                paragraphs = sec.split('\n\n')
                current_chunk = []
                current_count = 0

                for p in paragraphs:
                    p_words = p.split()
                    if current_count + len(p_words) > max_chunk_words and current_chunk:
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "section_title": section_title,
                            "content": chunk_text,
                            "token_estimate": int(current_count * 1.3),
                            "keywords": list(set(re.findall(r'\b[A-Za-z]{4,}\b', chunk_text.lower())))[:12]
                        })
                        chunk_idx += 1
                        current_chunk = [p]
                        current_count = len(p_words)
                    else:
                        current_chunk.append(p)
                        current_count += len(p_words)

                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "section_title": section_title,
                        "content": chunk_text,
                        "token_estimate": int(current_count * 1.3),
                        "keywords": list(set(re.findall(r'\b[A-Za-z]{4,}\b', chunk_text.lower())))[:12]
                    })
                    chunk_idx += 1

        return chunks

    def insert_document(
        self,
        page_id: str,
        title: str,
        raw_html: str,
        space_id: str = "",
        space_name: str = "",
        url: str = "",
        created_at: str = ""
    ) -> str:
        """Cleans, chunks, and indexes a Confluence page into the RAG database."""
        clean_md = self.html_to_clean_markdown(raw_html)
        words = clean_md.split()
        doc_id = f"doc_{page_id}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Upsert into documents
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    doc_id, space_id, space_name, page_id, title, url, created_at, char_count, word_count, raw_html, clean_markdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, space_id, space_name, page_id, title, url, created_at, len(clean_md), len(words), raw_html, clean_md
            ))

            # Delete old chunks if updating
            cursor.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM fts_chunks WHERE doc_id = ?", (doc_id,))

            # Chunk document
            chunks = self.chunk_document(title, clean_md)
            for ch in chunks:
                chunk_id = f"{doc_id}_ch{ch['chunk_index']}"
                cursor.execute("""
                    INSERT INTO document_chunks (
                        chunk_id, doc_id, chunk_index, section_title, content, token_estimate, keywords_json, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk_id, doc_id, ch["chunk_index"], ch["section_title"], ch["content"], ch["token_estimate"],
                    json.dumps(ch["keywords"]), json.dumps({"space": space_name, "page_id": page_id})
                ))

                # Insert into FTS5 index
                cursor.execute("""
                    INSERT INTO fts_chunks (chunk_id, doc_id, title, section_title, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (chunk_id, doc_id, title, ch["section_title"], ch["content"]))

            conn.commit()

        logger.info(f"Indexed document '{title}' (ID: {page_id}) into {len(chunks)} searchable chunks.")
        return doc_id

    def search_rag(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs full-text BM25 search against indexed document chunks."""
        # Sanitize query for FTS5 syntax
        clean_query = re.sub(r'[^\w\s]', ' ', query).strip()
        if not clean_query:
            return []

        fts_query = " OR ".join([f'"{w}"' for w in clean_query.split()])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    fts_chunks.chunk_id,
                    fts_chunks.doc_id,
                    fts_chunks.title,
                    fts_chunks.section_title,
                    fts_chunks.content,
                    bm25(fts_chunks) AS score,
                    documents.space_name,
                    documents.url
                FROM fts_chunks
                JOIN documents ON fts_chunks.doc_id = documents.doc_id
                WHERE fts_chunks MATCH ?
                ORDER BY score ASC
                LIMIT ?
            """, (fts_query, limit))

            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Returns total documents, chunks, and storage statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            total_chunks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT space_name) FROM documents")
            total_spaces = cursor.fetchone()[0]
            
            return {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "total_spaces": total_spaces,
                "db_path": self.db_path,
                "db_size_kb": round(os.path.getsize(self.db_path) / 1024, 2) if os.path.exists(self.db_path) else 0
            }
