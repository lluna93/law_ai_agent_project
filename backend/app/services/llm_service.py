import os
from openai import OpenAI
from app.prompts.legal_policy import LEGAL_SYSTEM_PROMPT


class LLMService:

    def __init__(self):
        self.client = OpenAI()

    def moderate(self, text: str):
        # OpenAI Moderation으로 기본 안전성 검사
        result = self.client.moderations.create(
            model="omni-moderation-latest",
            input=text
        )
        return result.results[0].flagged

    def generate(self, question: str, documents: list):

        # 검색 문서를 LLM 컨텍스트로 구성
        context = "\n\n".join(
            f"[{i}] 출처: {doc.source}\n{doc.content}"
            for i, doc in enumerate(documents, 1)
        )

        response = self.client.chat.completions.create(
            model=os.getenv("CHAT_MODEL", "gpt-4.1-mini"),
            messages=[
                {
                    "role": "system",
                    "content": LEGAL_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": (
                        f"검색된 법률 자료:\n{context}\n\n"
                        f"사용자 질문:\n{question}"
                    )
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content or ""