
import asyncio
import logging
import os

import httpx

from app.services.agent_service import AgentService


logger = logging.getLogger(__name__)

GRAPHRAG_URL = os.getenv(
    "GRAPHRAG_URL",
    "http://graphrag:8001/api/ask",
)


def get_field(obj, name, default=None):
    """dict 또는 객체에서 공통 방식으로 값 추출"""
    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def normalize_rag(result):
    """기존 RAG 응답을 GraphQL 타입에 맞게 변환"""
    sources = []

    for item in get_field(result, "sources", []) or []:
        sources.append({
            "source": str(
                get_field(item, "source", "") or ""
            ),
            "similarity": float(
                get_field(item, "similarity", 0) or 0
            ),
            "content": str(
                get_field(item, "content", "") or ""
            ),
        })

    return {
        "answer": str(
            get_field(result, "answer", "") or ""
        ),
        "status": str(
            get_field(result, "status", "SUCCESS")
        ),
        "sources": sources,
    }


def normalize_graph(result):
    """GraphRAG REST 응답을 GraphQL 타입에 맞게 변환"""
    sources = []

    for item in result.get("sources", []) or []:
        source_type = item.get("source_type") or []

        if isinstance(source_type, list):
            source_type = ", ".join(
                str(value) for value in source_type
            )

        sources.append({
            "source": str(
                item.get("source_id") or ""
            ),
            "similarity": float(
                item.get("score") or 0
            ),
            "content": str(
                item.get("text") or ""
            ),
            "source_type": str(source_type),
            "cited_articles": [
                str(value)
                for value in (
                    item.get("cited_articles") or []
                )
                if value is not None
            ],
            "concepts": [
                str(value)
                for value in (
                    item.get("concepts") or []
                )
                if value is not None
            ],
            "related_cases": [
                str(value)
                for value in (
                    item.get("related_cases") or []
                )
                if value is not None
            ],
        })

    return {
        "answer": str(result.get("answer") or ""),
        "status": str(
            result.get("status") or "SUCCESS"
        ),
        "sources": sources,
    }


def run_rag(question):
    return AgentService().consult(question)


async def run_graphrag(question):
    async with httpx.AsyncClient(
        timeout=180.0
    ) as client:

        response = await client.post(
            GRAPHRAG_URL,
            json={"question": question},
        )

        response.raise_for_status()
        return response.json()


async def compare_answers(question):
    """RAG와 GraphRAG를 동시에 실행"""

    rag_result, graph_result = await asyncio.gather(
        asyncio.to_thread(run_rag, question),
        run_graphrag(question),
        return_exceptions=True,
    )

    # RAG 결과
    if isinstance(rag_result, BaseException):
        logger.error(
            "RAG 실행 오류",
            exc_info=(
                type(rag_result),
                rag_result,
                rag_result.__traceback__,
            ),
        )

        rag = {
            "answer": "RAG 처리 중 오류가 발생했습니다.",
            "status": "ERROR",
            "sources": [],
        }
    else:
        try:
            rag = normalize_rag(rag_result)
        except Exception:
            logger.exception("RAG 응답 변환 오류")
            rag = {
                "answer": "RAG 응답 변환에 실패했습니다.",
                "status": "ERROR",
                "sources": [],
            }

    # GraphRAG 결과
    if isinstance(graph_result, BaseException):
        logger.error(
            "GraphRAG 실행 오류",
            exc_info=(
                type(graph_result),
                graph_result,
                graph_result.__traceback__,
            ),
        )

        graph = {
            "answer": "GraphRAG 처리 중 오류가 발생했습니다.",
            "status": "ERROR",
            "sources": [],
        }
    else:
        try:
            graph = normalize_graph(graph_result)
        except Exception:
            logger.exception("GraphRAG 응답 변환 오류")
            graph = {
                "answer": "GraphRAG 응답 변환에 실패했습니다.",
                "status": "ERROR",
                "sources": [],
            }

    return {
        "rag": rag,
        "graphrag": graph,
    }
