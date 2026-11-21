
import hashlib
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import MAX_CASES, MAX_LLM_CASES
from parser import parse_laws, parse_cases, parse_references
from graph_db import GraphDB
from extractor import extract_concepts
from embedding import GPUEmbeddings


# =========================================================
# 1. 로그 설정
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

log = logging.getLogger(__name__)


# =========================================================
# 2. CUDA GPU 임베딩 모델
# =========================================================

embeddings = GPUEmbeddings()


# =========================================================
# 3. 문서 분할 설정
# =========================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)


def create_chunks(node_id, text):
    """
    법률 또는 판례 문서를 청크로 분할합니다.

    반환:
        (chunk_id, parent_id, text)

    parent_id는 원본 Article 또는 Case의 ID입니다.
    """

    if not text or not text.strip():
        return

    documents = splitter.split_documents([
        Document(
            page_content=text,
            metadata={"parent_id": node_id},
        )
    ])

    for i, doc in enumerate(documents):

        chunk_id = hashlib.sha256(
            f"{node_id}:{i}:{doc.page_content}".encode(
                "utf-8"
            )
        ).hexdigest()

        # 반드시 3개 값을 반환
        yield (
            chunk_id,
            node_id,
            doc.page_content,
        )


# =========================================================
# 4. 기존 LLM 분석 여부 확인
# =========================================================

def has_concepts(db, node_id):
    """
    이미 법률 개념 관계가 생성된 판례인지 확인합니다.
    """

    result = db.execute(
        """
        MATCH (c:Case {id: $node_id})
              -[:HAS_CONCEPT]->(k:Concept)
        RETURN count(k) AS count
        """,
        node_id=node_id,
    )

    return bool(result and result[0]["count"] > 0)


# =========================================================
# 5. 기존 임베딩 여부 확인
# =========================================================

def has_embedding(db, chunk_id):
    """
    동일 청크의 CUDA 임베딩이 존재하는지 확인합니다.
    """

    result = db.execute(
        """
        MATCH (ch:Chunk {id: $chunk_id})
        RETURN
            ch.embedding_cuda IS NOT NULL AS exists,
            ch.embedding_model AS model
        """,
        chunk_id=chunk_id,
    )

    return bool(
        result
        and result[0]["exists"]
        and result[0]["model"] == "multilingual-e5-small"
    )


# =========================================================
# 6. GraphRAG 데이터 적재
# =========================================================

def ingest():

    db = GraphDB()

    try:

        # -------------------------------------------------
        # STEP 1. Neo4j 초기 설정
        # -------------------------------------------------

        log.info("STEP 1. Neo4j 인덱스 및 제약조건 확인")

        db.setup()

        # -------------------------------------------------
        # STEP 2. 법률 및 판례 TXT 파싱
        # -------------------------------------------------

        log.info("STEP 2. 법률 및 판례 TXT 파싱")

        articles = list(parse_laws())
        cases = list(parse_cases(MAX_CASES))

        log.info("법률 조문: %s개", len(articles))
        log.info("판례: %s개", len(cases))

        # -------------------------------------------------
        # STEP 3. 법률 조문 저장
        # -------------------------------------------------

        log.info("STEP 3. 법률 조문 Neo4j 저장")

        for i, article in enumerate(articles, 1):

            db.save_article(article)

            if i % 100 == 0:
                log.info(
                    "법률 저장 %s/%s",
                    i,
                    len(articles),
                )

        # -------------------------------------------------
        # STEP 4. 판례 및 참조조문 관계 저장
        # -------------------------------------------------

        log.info("STEP 4. 판례 및 참조조문 저장")

        for i, case in enumerate(cases, 1):

            db.save_case(case)

            article_ids = parse_references(
                case["references"]
            )

            for article_id in article_ids:
                db.save_reference(
                    case["id"],
                    article_id,
                )

            if i % 100 == 0:
                log.info(
                    "판례 저장 %s/%s",
                    i,
                    len(cases),
                )

        # -------------------------------------------------
        # STEP 5. OpenAI LLM 법률 개념 추출
        # -------------------------------------------------

        log.info("STEP 5. OpenAI LLM 법률 개념 분석")

        llm_cases = cases[:MAX_LLM_CASES]

        for i, case in enumerate(llm_cases, 1):

            # 기존 분석 결과가 있으면 재호출하지 않음
            if has_concepts(db, case["id"]):

                log.info(
                    "LLM 분석 건너뜀 %s/%s: %s",
                    i,
                    len(llm_cases),
                    case["number"],
                )

                continue

            content = (
                case["issues"]
                + "\n"
                + case["summary"]
            )

            if not content.strip():
                continue

            try:

                concepts = extract_concepts(content)

                if concepts:
                    db.save_concepts(
                        case["id"],
                        concepts,
                    )

                log.info(
                    "LLM 분석 %s/%s: %s",
                    i,
                    len(llm_cases),
                    concepts,
                )

            except Exception:
                log.exception(
                    "LLM 분석 실패: %s",
                    case["id"],
                )

        # -------------------------------------------------
        # STEP 6. 법률 및 판례 청크 생성
        # -------------------------------------------------

        log.info("STEP 6. 문서 청크 생성")

        items = []

        # 법률 조문 청크
        for article in articles:

            content = (
                f"{article['law']} "
                f"제{article['number']}조 "
                f"{article['title']}\n"
                f"{article['text']}"
            )

            items.extend(
                create_chunks(
                    article["id"],
                    content,
                )
            )

        # 판례 청크
        for case in cases:

            content = (
                f"사건번호: {case['number']}\n"
                f"사건명: {case['name']}\n"
                f"법원: {case['court']}\n"
                f"선고일자: {case['date']}\n"
                f"판시사항: {case['issues']}\n"
                f"판결요지: {case['summary']}"
            )

            items.extend(
                create_chunks(
                    case["id"],
                    content,
                )
            )

        log.info("전체 청크: %s개", len(items))

        if items:
            log.info(
                "첫 번째 청크 튜플 요소 수: %s",
                len(items[0]),
            )

        # -------------------------------------------------
        # STEP 7. 기존 임베딩 제외
        # -------------------------------------------------

        log.info("STEP 7. 기존 CUDA 임베딩 확인")

        pending_items = []

        for item in items:

            chunk_id, parent_id, text = item

            if not has_embedding(db, chunk_id):
                pending_items.append(item)

        log.info(
            "전체 %s개 중 신규 임베딩 %s개",
            len(items),
            len(pending_items),
        )

        # -------------------------------------------------
        # STEP 8. CUDA GPU 임베딩 생성 및 Neo4j 저장
        # -------------------------------------------------

        log.info("STEP 8. CUDA GPU 임베딩 시작")

        batch_size = 50

        total = len(pending_items)

        for start in range(0, total, batch_size):

            batch = pending_items[
                start:start + batch_size
            ]

            # item = (chunk_id, parent_id, text)
            texts = [
                item[2] for item in batch
            ]

            # CUDA GPU 임베딩
            vectors = embeddings.embed_documents(
                texts
            )

            # Neo4j에 벡터 저장
            for (
                chunk_id,
                parent_id,
                text,
            ), vector in zip(batch, vectors):

                db.save_chunk(
                    chunk_id,
                    parent_id,
                    text,
                    vector,
                )

            completed = min(
                start + batch_size,
                total,
            )

            log.info(
                "CUDA 임베딩 저장 %s/%s (%.1f%%)",
                completed,
                total,
                completed / total * 100,
            )

        # -------------------------------------------------
        # STEP 9. 적재 결과 확인
        # -------------------------------------------------

        log.info("STEP 9. Neo4j 적재 결과 확인")

        result = db.execute(
            """
            MATCH (n)
            RETURN
                labels(n) AS type,
                count(n) AS count
            ORDER BY count DESC
            """
        )

        for row in result:
            log.info(
                "%s: %s개",
                row["type"],
                row["count"],
            )

        log.info("GraphRAG 데이터 구축 완료!")

    finally:
        db.close()


# =========================================================
# 7. 실행
# =========================================================

if __name__ == "__main__":
    ingest()
