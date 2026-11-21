import os
from openai import OpenAI


class EmbeddingService:

    def __init__(self):
        self.client = OpenAI()

    def embed(self, text: str):
        # 질문을 1536차원 벡터로 변환
        result = self.client.embeddings.create(
            model=os.getenv(
                "EMBEDDING_MODEL",
                "text-embedding-3-small"
            ),
            input=text
        )

        return result.data[0].embedding