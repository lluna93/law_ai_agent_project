import os
import psycopg
from pgvector.psycopg import register_vector


def connect():
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    register_vector(conn)
    return conn


def init_db():
    # pgvector 확장 생성 후 벡터 타입 테이블 생성
    with psycopg.connect(
        os.environ["DATABASE_URL"],
        autocommit=True
    ) as conn:

        conn.execute(
            "CREATE EXTENSION IF NOT EXISTS vector"
        )

        conn.execute("""
            CREATE TABLE IF NOT EXISTS law_chunks (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR(1536) NOT NULL,
                UNIQUE(source, chunk_index)
            )
        """)