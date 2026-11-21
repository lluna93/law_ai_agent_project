from app.repositories.law_repository import LawRepository
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


class AgentService:

    def __init__(self):
        self.repository = LawRepository()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()

    def consult(self, question: str):
        # 1. 사용자 질문 안전성 검사
        if self.llm_service.moderate(question):
            return {
                "answer": "안전 정책에 따라 해당 요청에 답변할 수 없습니다.",
                "status": "BLOCKED",
                "sources": [],
            }

        # 2. 질문을 임베딩 벡터로 변환
        question_vector = self.embedding_service.embed(question)

        # 3. PostgreSQL pgvector에서 유사 문서 검색
        documents = self.repository.search_similar(
            question_vector,
            limit=5,
        )

        # 4. 검색 결과가 없는 경우
        if not documents:
            return {
                "answer": "관련 법률 자료를 찾지 못했습니다.",
                "status": "NO_CONTEXT",
                "sources": [],
            }

        # 5. 검색된 법률 자료를 LLM에 전달
        answer = self.llm_service.generate(
            question,
            documents,
        )

        # 6. LLM 답변 안전성 검사
        if self.llm_service.moderate(answer):
            return {
                "answer": "답변을 안전하게 제공할 수 없습니다.",
                "status": "BLOCKED",
                "sources": [],
            }

        # 7. AI 답변 + 검색 출처 + 원문 반환
        return {
            "answer": answer,
            "status": "SUCCESS",
            "sources": [
                {
                    "source": doc.source,
                    "similarity": doc.similarity,
                    "content": doc.content,
                }
                for doc in documents
            ],
        }