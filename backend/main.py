from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from app.database import init_db
from app.graphql.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 DB 테이블 확인
    init_db()
    yield


app = FastAPI(
    title="Law AI GraphQL Agent",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_methods=["*"],
    allow_headers=["*"]
)

# GraphQL 엔드포인트
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health():
    return {"status": "ok"}