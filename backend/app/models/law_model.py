from dataclasses import dataclass


@dataclass
class LawChunk:
    # pgvector 검색 결과 모델
    id: int
    source: str
    content: str
    similarity: float