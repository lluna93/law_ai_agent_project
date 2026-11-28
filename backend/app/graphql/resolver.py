
import strawberry
from fastapi.concurrency import run_in_threadpool

from app.graphql.inputs import ConsultInput
from app.graphql.types import (
    LawSourceType,
    ConsultResultType,
    GraphSourceType,
    GraphConsultResultType,
    CompareResultType,
)
from app.services.agent_service import AgentService
from app.services.compare_service import (
    compare_answers,
    normalize_rag,
)


def to_rag_type(result: dict) -> ConsultResultType:
    return ConsultResultType(
        answer=result["answer"],
        status=result["status"],
        sources=[
            LawSourceType(**source)
            for source in result["sources"]
        ],
    )


def to_graph_type(result: dict) -> GraphConsultResultType:
    return GraphConsultResultType(
        answer=result["answer"],
        status=result["status"],
        sources=[
            GraphSourceType(**source)
            for source in result["sources"]
        ],
    )


def validate_question(question: str, max_length: int):
    question = question.strip()

    if not question or len(question) > max_length:
        raise ValueError(
            f"상담 내용은 1~{max_length}자로 입력해주세요."
        )

    return question


@strawberry.type
class Query:

    @strawberry.field
    def health(self) -> str:
        return "Law AI Agent Running"


@strawberry.type
class Mutation:

    # 기존 RAG 상담
    @strawberry.mutation
    async def consult_law(
        self,
        input: ConsultInput,
    ) -> ConsultResultType:

        question = validate_question(
            input.question, 4000
        )

        result = await run_in_threadpool(
            AgentService().consult,
            question,
        )

        return to_rag_type(normalize_rag(result))

    # 신규: RAG + GraphRAG 비교 상담
    @strawberry.mutation
    async def consult_both(
        self,
        input: ConsultInput,
    ) -> CompareResultType:

        question = validate_question(
            input.question, 2000
        )

        result = await compare_answers(question)

        return CompareResultType(
            rag=to_rag_type(result["rag"]),
            graphrag=to_graph_type(result["graphrag"]),
        )
