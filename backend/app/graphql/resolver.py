import strawberry

from fastapi.concurrency import run_in_threadpool

from app.graphql.inputs import ConsultInput
from app.graphql.types import (
    LawSourceType,
    ConsultResultType,
)
from app.services.agent_service import AgentService


@strawberry.type
class Query:

    @strawberry.field
    def health(self) -> str:
        # GraphQL 서버 상태 확인
        return "Law AI Agent Running"


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def consult_law(
        self,
        input: ConsultInput,
    ) -> ConsultResultType:

        question = input.question.strip()

        # 입력값 검증
        if not question:
            raise ValueError("상담 내용을 입력해주세요.")

        if len(question) > 4000:
            raise ValueError("상담 내용은 4000자 이하로 입력해주세요.")

        # 동기식 RAG/LLM 작업을 별도 스레드에서 실행
        result = await run_in_threadpool(
            AgentService().consult,
            question,
        )

        # Python 결과를 GraphQL 타입으로 변환
        sources = [
            LawSourceType(
                source=item["source"],
                similarity=item["similarity"],
                content=item["content"],
            )
            for item in result["sources"]
        ]

        return ConsultResultType(
            answer=result["answer"],
            status=result["status"],
            sources=sources,
        )