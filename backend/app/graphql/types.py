import strawberry


@strawberry.type
class LawSourceType:
    # RAG 검색 결과
    source: str
    similarity: float
    content: str


@strawberry.type
class ConsultResultType:
    # 법률 AI 상담 결과
    answer: str
    status: str
    sources: list[LawSourceType]