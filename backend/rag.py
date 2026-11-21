import os
from openai import OpenAI
from db import connect

client = OpenAI()


def ask(question: str):

    # 1. 사용자 질문을 임베딩
    vector = client.embeddings.create(
        model=os.getenv(
            "EMBEDDING_MODEL",
            "text-embedding-3-small"
        ),
        input=question
    ).data[0].embedding

    # 2. pgvector에서 유사한 문서 TOP 5 검색
    with connect() as conn:

        rows = conn.execute(
            """
            SELECT
                source,
                content,
                1 - (embedding <=> %s) AS similarity
            FROM law_chunks
            ORDER BY embedding <=> %s
            LIMIT 5
            """,
            (vector, vector)
        ).fetchall()

    if not rows:
        return {
            "answer": "검색 가능한 법률 문서가 없습니다. 먼저 임베딩을 실행하세요.",
            "sources": []
        }

    # 3. 검색된 법률 문서를 LLM 문맥으로 구성
    context = "\n\n".join(
        f"[{i}] 출처: {r[0]}\n{r[1]}"
        for i, r in enumerate(rows, 1)
    )

    # 4. 검색된 문서에 근거하여 답변 생성
    response = client.chat.completions.create(
        model=os.getenv(
            "CHAT_MODEL",
            "gpt-4.1-mini"
        ),
        messages=[
            {
                "role": "system",
                "content": (
                    "법률 문서 검색 도우미입니다. "
                    "제공된 문맥만 근거로 답하세요. "
                    "근거가 부족하면 모른다고 답하세요. "
                    "출처 번호를 표시하고 "
                    "법률 자문이 아님을 명시하세요."
                )
            },
            {
                "role": "user",
                "content": (
                    f"문맥:\n{context}\n\n"
                    f"질문: {question}"
                )
            }
        ]
    )

    # 5. 답변 및 출처 반환
    return {
        "answer": response.choices[0].message.content,
        "sources": [
            {
                "source": r[0],
                "similarity": round(float(r[2]), 4)
            }
            for r in rows
        ]
    }