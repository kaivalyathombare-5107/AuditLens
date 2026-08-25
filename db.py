import os
from contextlib import contextmanager
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add your Neon PostgreSQL connection "
        "string to the .env file."
    )


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT,
                    file_bytes BYTEA,
                    extracted_text TEXT,
                    predicted_category TEXT,
                    model_confidence DOUBLE PRECISION,
                    duplicate_hash TEXT,
                    sender_alias TEXT,
                    processing_status TEXT,
                    reviewer_category TEXT,
                    reviewer_alias TEXT,
                    tokens_used INTEGER,
                    synopsis TEXT,
                    error TEXT,
                    uploaded_at TIMESTAMPTZ
                )
            """)
        conn.commit()


def insert_document(doc: dict, file_bytes: bytes = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents
                (document_id, filename, file_bytes, extracted_text,
                 predicted_category, model_confidence, duplicate_hash,
                 sender_alias, processing_status, reviewer_category,
                 reviewer_alias, tokens_used, synopsis, error, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    file_bytes = EXCLUDED.file_bytes,
                    extracted_text = EXCLUDED.extracted_text,
                    predicted_category = EXCLUDED.predicted_category,
                    model_confidence = EXCLUDED.model_confidence,
                    duplicate_hash = EXCLUDED.duplicate_hash,
                    sender_alias = EXCLUDED.sender_alias,
                    processing_status = EXCLUDED.processing_status,
                    reviewer_category = EXCLUDED.reviewer_category,
                    reviewer_alias = EXCLUDED.reviewer_alias,
                    tokens_used = EXCLUDED.tokens_used,
                    synopsis = EXCLUDED.synopsis,
                    error = EXCLUDED.error,
                    uploaded_at = EXCLUDED.uploaded_at
            """, (
                doc["document_id"],
                doc["filename"],
                file_bytes,
                doc["extracted_text"],
                doc["predicted_category"],
                doc["model_confidence"],
                doc["duplicate_hash"],
                doc["sender_alias"],
                doc["processing_status"],
                doc["reviewer_category"],
                doc["reviewer_alias"],
                doc["tokens_used"],
                doc["synopsis"],
                doc.get("error"),
                datetime.now(),
            ))
        conn.commit()


def update_document(document_id, **fields):
    """Update just the given fields."""
    if not fields:
        return

    allowed_fields = {
        "filename",
        "file_bytes",
        "extracted_text",
        "predicted_category",
        "model_confidence",
        "duplicate_hash",
        "sender_alias",
        "processing_status",
        "reviewer_category",
        "reviewer_alias",
        "tokens_used",
        "synopsis",
        "error",
        "uploaded_at",
    }

    invalid = set(fields) - allowed_fields
    if invalid:
        raise ValueError(f"Invalid document fields: {', '.join(sorted(invalid))}")

    set_clause = ", ".join(f'"{k}" = %s' for k in fields)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'UPDATE documents SET {set_clause} WHERE document_id = %s',
                (*fields.values(), document_id),
            )
        conn.commit()


def fetch_all_documents():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM documents ORDER BY uploaded_at")
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def fetch_file_bytes(document_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT file_bytes, filename FROM documents WHERE document_id = %s",
                (document_id,),
            )
            row = cur.fetchone()
            return (
                (bytes(row["file_bytes"]), row["filename"])
                if row and row["file_bytes"] is not None
                else (None, row["filename"]) if row else (None, None)
            )
