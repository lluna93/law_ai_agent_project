from neo4j import GraphDatabase
from config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
)


class GraphDB:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def execute(self, query, **params):
        with self.driver.session() as session:
            return [
                record.data()
                for record in session.run(
                    query, **params
                )
            ]

    def setup(self):
        for label in [
            "Law", "Article", "Case", "Concept"
        ]:
            self.execute(
                f"CREATE CONSTRAINT {label.lower()}_id "
                f"IF NOT EXISTS FOR (n:{label}) "
                "REQUIRE n.id IS UNIQUE"
            )

        self.execute("""
        CREATE CONSTRAINT chunk_id IF NOT EXISTS
        FOR (n:Chunk) REQUIRE n.id IS UNIQUE
        """)

        self.execute("""
        CREATE VECTOR INDEX legal_vector_cuda
        IF NOT EXISTS
        FOR (n:Chunk) ON (n.embedding_cuda)
        OPTIONS {indexConfig: {
          `vector.dimensions`: 384,
          `vector.similarity_function`: 'cosine'
        }}
        """)

    def save_article(self, article):
        self.execute("""
        MERGE (l:Law {id: $law})
        SET l.name = $law

        MERGE (a:Article {id: $id})
        SET a += $props

        MERGE (l)-[:HAS_ARTICLE]->(a)
        """,
        law=article["law"],
        id=article["id"],
        props=article)

    def save_case(self, case):
        self.execute("""
        MERGE (c:Case {id: $id})
        SET c += $props
        """, id=case["id"], props=case)

    def save_reference(
        self, case_id, article_id
    ):
        self.execute("""
        MATCH (c:Case {id: $case_id})
        MATCH (a:Article {id: $article_id})
        MERGE (c)-[:CITES]->(a)
        """,
        case_id=case_id,
        article_id=article_id)

    def save_concepts(
        self, node_id, concepts
    ):
        self.execute("""
        MATCH (n)
        WHERE (n:Case OR n:Article)
          AND n.id = $node_id

        UNWIND $concepts AS name

        MERGE (k:Concept {id: name})
        SET k.name = name

        MERGE (n)-[:HAS_CONCEPT {
          origin: 'LLM'
        }]->(k)
        """,
        node_id=node_id,
        concepts=concepts)

    def save_chunk(
        self, chunk_id, parent_id, text, vector
    ):
        self.execute("""
        MATCH (n)
        WHERE (n:Case OR n:Article)
          AND n.id = $parent_id

        MERGE (ch:Chunk {id: $chunk_id})
        SET ch.text = $text,
            ch.embedding_cuda = $vector,
            ch.embedding_model = 'multilingual-e5-small'

        MERGE (n)-[:HAS_CHUNK]->(ch)
        """,
        chunk_id=chunk_id,
        parent_id=parent_id,
        text=text,
        vector=vector)