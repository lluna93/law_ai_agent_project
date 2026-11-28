
import strawberry


@strawberry.type
class LawSourceType:
    source: str
    similarity: float
    content: str


@strawberry.type
class ConsultResultType:
    answer: str
    status: str
    sources: list[LawSourceType]


@strawberry.type
class GraphSourceType:
    source: str
    similarity: float
    content: str
    source_type: str
    cited_articles: list[str]
    concepts: list[str]
    related_cases: list[str]


@strawberry.type
class GraphConsultResultType:
    answer: str
    status: str
    sources: list[GraphSourceType]


@strawberry.type
class CompareResultType:
    rag: ConsultResultType
    graphrag: GraphConsultResultType
