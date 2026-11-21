import os
from pathlib import Path
from openai import OpenAI

from app.database import init_db, get_connection


client = OpenAI()
BASE = Path(__file__).resolve().parent

MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-3-small"
)


def split_text(text, size=900, overlap=150):
    # 일정 길이로 나누고 문맥 일부 중첩
    step = size - overlap

    return [
        text[i:i + size]
        for i in range(0, len(text), step)
        if text[i:i + size].strip()
    ]


def run():
    init_db()

    # 법률 TXT 파일 검색
    files = [
        p for p in BASE.rglob("*.txt")
        if ".venv" not in p.parts
        and "node_modules" not in p.parts
    ]

    with get_connection() as conn:

        for path in sorted(files):
            source = path.relative_to(BASE).as_posix()

            text = path.read_text(encoding="utf-8-sig")
            chunks = split_text(text)

            if not chunks:
                continue

            # API 요청을 먼저 완료한 후 DB 반영
            embeddings = []

            for start in range(0, len(chunks), 100):
                batch = chunks[start:start + 100]

                response = client.embeddings.create(
                    model=MODEL,
                    input=batch
                )

                embeddings.extend(
                    item.embedding
                    for item in sorted(
                        response.data,
                        key=lambda item: item.index
                    )
                )

            # 문서 단위 트랜잭션
            with conn.transaction():

                conn.execute(
                    "DELETE FROM law_chunks WHERE source = %s",
                    (source,)
                )

                for i, (chunk, vector) in enumerate(
                    zip(chunks, embeddings)
                ):
                    conn.execute(
                        """
                        INSERT INTO law_chunks
                        (source, chunk_index, content, embedding)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (source, i, chunk, vector)
                    )

            print(f"Indexed {source}: {len(chunks)} chunks")


if __name__ == "__main__":
    run()