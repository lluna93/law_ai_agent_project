from app.database import get_connection
from app.models.law_model import LawChunk


class LawRepository:

    def search_similar(self, vector, limit=5):
        # OpenAI Embedding 결과를 pgvector 문자열로 변환
        vector_str = "[" + ",".join(map(str, vector)) + "]"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        source,
                        content,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM law_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (vector_str, vector_str, limit),
                )

                rows = cur.fetchall()

        # 검색된 원문(content)을 포함하여 반환
        return [
            LawChunk(
                id=row[0],
                source=row[1],
                content=row[2],
                similarity=float(row[3]),
            )
            for row in rows
        ]