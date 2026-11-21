
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from embedding import GPUEmbeddings
from config import OPENAI_MODEL, EMBEDDING_MODEL
from graph_db import GraphDB

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
embeddings = GPUEmbeddings()
answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """
당신은 한국 법률 정보 검색 도우미입니다.
반드시 제공된 검색 근거에 기반하여 답변하세요.

- 법률 조문과 판례를 구분하세요.
- 사건번호와 조문번호를 명시하세요.
- 확인되지 않은 법률 관계는 추측하지 마세요.
- 자료가 부족하면 부족하다고 답하세요.
- 과거 판례와 현재 법률의 적용 시점 차이에 주의하세요.
- 법률 자문이나 확정적 판결 예측처럼 표현하지 마세요.
"""),
    ("human", "질문: {question}\n\n검색 근거:\n{context}")
])

answer_chain = answer_prompt | llm


def search_graph(question, top_k=5):
    vector = embeddings.embed_query(question)
    db = GraphDB()

    try:
        rows = db.execute("""
        CALL db.index.vector.queryNodes(
         'legal_vector_cuda', $top_k, $vector
        )
        YIELD node AS ch, score

        MATCH (parent)-[:HAS_CHUNK]->(ch)

        OPTIONAL MATCH (parent)-[:CITES]->(article:Article)
        OPTIONAL MATCH (parent)-[:HAS_CONCEPT]->(concept:Concept)
        OPTIONAL MATCH (related:Case)-[:HAS_CONCEPT]->(concept)

        RETURN
            parent.id AS source_id,
            labels(parent) AS source_type,
            ch.text AS text,
            score,
            collect(DISTINCT article.id)[..10] AS cited_articles,
            collect(DISTINCT concept.name)[..10] AS concepts,
            collect(DISTINCT related.id)[..5] AS related_cases

        ORDER BY score DESC
        """, top_k=top_k, vector=vector)

        return rows
    finally:
        db.close()


def ask(question):
    results = search_graph(question)

    if not results:
        return {
            "answer": "관련 법률 근거를 찾지 못했습니다.",
            "sources": [],
        }

    contexts = []

    for row in results:
        contexts.append(
            f"[출처: {row['source_id']}]\n"
            f"원문: {row['text']}\n"
            f"참조조문: {row['cited_articles']}\n"
            f"법률개념: {row['concepts']}\n"
            f"관련판례 ID: {row['related_cases']}"
        )

    response = answer_chain.invoke({
        "question": question,
        "context": "\n\n".join(contexts),
    })

    return {
        "answer": response.content,
        "sources": results,
    }
