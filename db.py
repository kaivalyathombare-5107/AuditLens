import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "documind.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name, like a dict
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT,
                file_bytes BLOB,
                extracted_text TEXT,
                predicted_category TEXT,
                model_confidence REAL,
                duplicate_hash TEXT,
                sender_alias TEXT,
                processing_status TEXT,
                reviewer_category TEXT,
                reviewer_alias TEXT,
                tokens_used INTEGER,
                synopsis TEXT,
                error TEXT,
                uploaded_at TEXT
            )
        """)
        conn.commit()


def insert_document(doc: dict, file_bytes: bytes = None):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO documents
            (document_id, filename, file_bytes, extracted_text, predicted_category,
             model_confidence, duplicate_hash, sender_alias, processing_status,
             reviewer_category, reviewer_alias, tokens_used, synopsis, error, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc["document_id"], doc["filename"], file_bytes, doc["extracted_text"],
            doc["predicted_category"], doc["model_confidence"], doc["duplicate_hash"],
            doc["sender_alias"], doc["processing_status"], doc["reviewer_category"],
            doc["reviewer_alias"], doc["tokens_used"], doc["synopsis"], doc.get("error"),
            datetime.now().isoformat(),
        ))
        conn.commit()


def update_document(document_id, **fields):
    """Update just the given fields, e.g. update_document(id, processing_status='Verified')."""
    with get_conn() as conn:
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE documents SET {set_clause} WHERE document_id = ?",
            (*fields.values(), document_id),
        )
        conn.commit()


def fetch_all_documents():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at").fetchall()
        return [dict(r) for r in rows]


def fetch_file_bytes(document_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT file_bytes, filename FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
        return (row["file_bytes"], row["filename"]) if row else (None, None)
