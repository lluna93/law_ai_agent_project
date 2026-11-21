# ⚖️ Law AI Agent

**React + FastAPI + GraphQL 기반 법률 정보 검색·상담 프로젝트 — RAG(pgvector)와 GraphRAG(Neo4j) 비교**

하나의 법률 질문에 대해 **RAG(문서 유사도 검색)**와 **GraphRAG(벡터 검색 + 법률 지식 관계 확장)**가 독립적으로 답변하도록 설계했습니다. Docker 환경에서 **`consultBoth` GraphQL Mutation 및 React 비교 화면의 실제 실행을 확인**했습니다. 아래에는 최신 통합 아키텍처, 최초 데이터 구축과 질문 처리 흐름, 로컬 학습 환경 구성 방법을 정리했습니다.

> ⚠️ 이 프로젝트는 법률 정보 탐색을 위한 데모이며 변호사의 법률 자문을 대체하지 않습니다. 저장된 판례 청크는 판결문 전체가 아닐 수 있으며, 공식 판례 직접 링크는 검증된 사건번호·URL 메타데이터가 있을 때만 제공할 수 있습니다.

## 🏗️ 시스템 아키텍처

![Law AI Agent 시스템 아키텍처](assets/architecture.png)

> **최신 통합 아키텍처:** Docker Compose의 `nginx`, `backend`, `graphrag`, `db`, `neo4j` 5개 서비스로 구성됩니다. 외부에 공개되는 포트는 기본적으로 Nginx의 80번이며, DB 및 내부 API 포트는 Docker 네트워크 내부에서 사용합니다. GraphRAG `/api/ask`는 메인 백엔드가 내부 HTTP로 호출합니다. 이미지의 서비스별 포트는 내부 리스닝 포트를 포함한 개념 표시이며, 실제 포트 공개 여부는 `docker-compose.yml`을 기준으로 확인하세요. 답변 모델은 `.env`의 `CHAT_MODEL`/`OPENAI_MODEL` 설정을 따릅니다.

- **Nginx**: React(Vite) 정적 파일 제공 및 `/graphql`, `/health`를 FastAPI로 리버스 프록시
- **FastAPI + Strawberry GraphQL**: 기존 `consultLaw` 및 통합 `consultBoth` Mutation
- **OpenAI**: 질문 임베딩 및 검색 근거 기반 답변 생성
- **PostgreSQL + pgvector**: 법령·판례 청크 및 임베딩 벡터 영속 저장
- **Docker Compose**: Nginx / RAG Backend / GraphRAG Backend / PostgreSQL / Neo4j 서비스와 내부 네트워크 관리

## 🔎 RAG vs GraphRAG — 두 검색 방식 비교

![RAG와 GraphRAG 비교 인포그래픽](assets/rag-vs-graphrag.png)

| 비교 항목 | RAG | GraphRAG |
| --- | --- | --- |
| 저장소 | PostgreSQL + pgvector | Neo4j |
| 질문 임베딩 | OpenAI `text-embedding-3-small` (1536차원) | `intfloat/multilingual-e5-small` (384차원) |
| 검색 방법 | 의미적으로 가까운 법률 문서 청크 TOP 5 | Neo4j 벡터 인덱스 검색 후 연결된 조문·개념·판례 관계 확장 |
| 근거 | 문서 청크의 텍스트 | 문서 청크 + 그래프에 저장된 관계 정보 |
| 장점 | 구현 단순, 문서 원문 검색에 적합 | 관련 법률 개념과 판례의 연결 맥락을 추가로 탐색 |
| 주의 | 청크 간 관계를 직접 추론하기 어려움 | 그래프 추출 품질 및 관계의 정확도에 의존 |

> **중요:** GraphRAG의 `related_cases`는 공유 개념을 통해 연결된 판례를 의미할 수 있으며, 반드시 판례 간 **직접 인용 관계**를 의미하지 않습니다. 두 방식 중 어느 것이 더 정확한지는 실제 질문·정답 데이터로 평가해야 합니다.

### 최초 준비 과정 vs 질문 처리 과정

| 단계 | RAG (PostgreSQL + pgvector) | GraphRAG (Neo4j) |
| --- | --- | --- |
| **최초 준비 ① 수집** | 법령·판례 원문 수집 | 법령·판례 원문 수집 |
| **최초 준비 ② 가공** | 원문을 청크로 분할 | 조문·판례·개념을 추출하고 관계(`CITES`, `HAS_CONCEPT` 등)를 구성하며 청크로 분할 |
| **최초 준비 ③ 임베딩** | 청크를 OpenAI `text-embedding-3-small`로 1536차원 임베딩 | 청크를 `multilingual-e5-small`로 384차원 임베딩 |
| **최초 준비 ④ 저장** | `law_chunks`의 텍스트·벡터를 pgvector에 저장 | Neo4j에 노드·관계·청크 벡터를 저장하고 벡터 인덱스 구성 |
| **질문 처리 ① 임베딩** | 새 질문만 OpenAI 임베딩 | 새 질문만 E5 임베딩 |
| **질문 처리 ② 검색** | pgvector 코사인 거리로 유사 청크 TOP 5 검색 | Neo4j 벡터 인덱스로 유사 청크 검색 |
| **질문 처리 ③ 근거 확장** | 검색된 청크 사용 | 검색된 청크의 부모 노드에서 조문·개념·관련 판례 관계 탐색 |
| **질문 처리 ④ 생성** | 청크를 근거로 LLM 답변 생성 | 청크와 그래프 관계 정보를 근거로 LLM 답변 생성 |

**핵심:** 최초 준비 시 저장한 문서 임베딩과 지식 그래프를 질문마다 다시 만들지 않습니다. 질문 텍스트만 새로 임베딩하고 기존 저장소를 검색합니다. GraphRAG도 **벡터 검색을 먼저 수행**하며, 여기에 관계 탐색이 추가됩니다.

```text
[최초 준비]
RAG:      법률 원문 → 청크 → OpenAI 임베딩 → PostgreSQL/pgvector
GraphRAG: 법률 원문 → 조문·판례·개념/관계 추출 ─┐
                   └→ 청크 → E5 임베딩 ──────┴→ Neo4j

[질문 시]
RAG:      질문 → OpenAI 임베딩 → pgvector 유사도 검색 → LLM 답변
GraphRAG: 질문 → E5 임베딩 → Neo4j 벡터 검색 → 관계 확장 → LLM 답변
```

### 통합 상담 처리 흐름

```text
React: 질문 1회 입력
    ↓ GraphQL consultBoth
FastAPI: compare_service.py (병렬 실행)
    ├─ RAG: OpenAI 임베딩 → pgvector 유사도 검색 → LLM 답변
    └─ GraphRAG: E5 임베딩 → Neo4j 벡터 검색 → 관계 확장 → LLM 답변
    ↓
React: RAG 답변 / GraphRAG 답변 / 각 방식의 검색 근거 비교
```

### GraphRAG 통합 관련 파일

```text
law_ai_agent_project/
├── backend/app/services/compare_service.py  # 두 검색 방식 병렬 호출
├── backend/app/graphql/                    # consultBoth GraphQL Mutation
├── graphrag_backend/
│   ├── main.py                              # POST /api/ask
│   ├── rag.py                               # Neo4j 벡터·관계 검색
│   ├── embedding.py                         # multilingual-e5-small
│   ├── graph_db.py                          # Neo4j 연결·Cypher
│   ├── parser.py / extractor.py / ingest.py # 수동 적재 전용
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/src/pages/AgentPage.jsx         # 비교 상담 입력 화면
└── frontend/src/components/agent/CompareAnswer.jsx
```

### 데이터 보존 및 실행 확인

- PostgreSQL 볼륨: `PGVECTOR_VOLUME_NAME`으로 기존 pgvector 데이터 재사용
- Neo4j 볼륨: `NEO4J_VOLUME_NAME`으로 기존 그래프 데이터 재사용. 기존 Neo4j와 새 컨테이너가 동일 `/data` 볼륨을 동시에 사용하지 않도록 주의
- `ingest.py`는 서비스 시작 시 자동 실행하지 않음
- PostgreSQL `pg_dump` 파일에는 **Neo4j 그래프 데이터가 포함되지 않으므로** Neo4j 백업은 별도 필요
- 기존 데이터 볼륨을 지우는 `docker compose down -v` 명령은 사용하지 않음

```powershell
docker volume ls
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend graphrag
```

> **실행 상태(2026-11-21):** 로컬 Docker에서 `consultBoth`가 `rag.status = SUCCESS`, `graphrag.status = SUCCESS`를 반환하는 것을 확인했고, React 화면에서도 두 답변과 각각의 출처 TOP 5가 표시되는 것을 확인했습니다. 두 상태값은 API 실행 성공을 뜻하며, 법률적 정확성을 검증한 지표는 아닙니다.

## 🧪 통합 실행 확인 및 비교 관찰

2026-11-21 로컬 Docker 환경에서 `consultBoth` Mutation 호출 시 **RAG와 GraphRAG 모두 `SUCCESS`** 응답을 확인했습니다. React 화면에서 두 답변과 각 검색 출처 TOP 5를 나란히 표시했습니다. 다만 실행 화면 캡처는 문서를 간결하게 유지하기 위해 README에서 제외했습니다.

- **RAG:** 법률 문서 청크 유사도 검색을 기반으로 답변
- **GraphRAG:** 유사 청크 검색 후 관련 조문·법률 개념·판례 관계를 확장하여 답변
- **관찰:** 한 테스트 질문에서 GraphRAG의 근거 제시 방식이 더 만족스러웠습니다. 이는 단일 사례의 주관적 평가이며 법률 정확도 우위를 뜻하지 않습니다.
- **주의:** 두 방식의 유사도 점수는 임베딩 모델이 달라 직접 비교할 수 없으며, 생성된 사건번호·법률 근거는 공식 자료로 검증해야 합니다.

### 통합 GraphQL 요청 예시

```graphql
mutation {
  consultBoth(input: { question: "AI가 생성한 글의 저작권은 누구에게 있나요?" }) {
    rag { status answer sources { source similarity content } }
    graphrag {
      status
      answer
      sources { source similarity content sourceType citedArticles concepts relatedCases }
    }
  }
}
```

## ✨ 주요 기능

| 기능 | 설명 |
| --- | --- |
| 법률 상담 | 자연어 질문에 대한 검색 근거 기반 AI 답변 |
| RAG 검색 | 질문 임베딩과 pgvector 코사인 거리로 유사 청크 TOP 5 조회 |
| 검색 출처 | 출처 파일명, 유사도, 검색된 원문 청크 표시 |
| 원문 확인 | AG Grid 행 클릭 시 Modal에서 DB에 저장된 청크 확인 |
| GraphQL API | Strawberry GraphQL의 `consultLaw`, `consultBoth`, `health` |
| 통합 비교 상담 | 동일 질문으로 RAG·GraphRAG 병렬 실행, 답변 2열 비교 |
| GraphRAG 검색 | Neo4j 벡터 인덱스 검색 및 조문·개념·판례 관계 확장 |
| 컨테이너 배포 | Nginx + FastAPI 2개 + PostgreSQL + Neo4j를 Docker Compose로 실행 |

## 🧰 기술 스택

| 영역 | 기술 |
| --- | --- |
| Frontend | React, Vite, Ant Design, AG Grid, styled-components |
| Backend | Python, FastAPI, Strawberry GraphQL |
| RAG | OpenAI Embedding, LLM, pgvector |
| GraphRAG | multilingual-e5-small, Neo4j, LangChain, OpenAI LLM |
| Database | PostgreSQL 16 + pgvector, Neo4j 5.26 |
| Infra | Docker, Docker Compose, Nginx |

## 📂 프로젝트 구조

```text
law_ai_agent_project/
├── .env                         # 로컬 비밀 설정 (Git에 올리지 않음)
├── .env.example                 # 공유 가능한 환경변수 예시
├── .gitignore                   # 비밀 설정·백업·생성 파일 제외
├── data/                        # 이용 조건 확인된 공개 법률 학습 데이터
│   ├── README.md                # 데이터 출처 및 사용 규칙
│   ├── sources.csv              # 데이터 출처·라이선스 기록 템플릿
│   ├── statutes/                # 법령 원문 (검증 후 추가)
│   └── cases/                   # 판결문 원문 (검증 후 추가)
├── docker-compose.yml           # nginx, backend, graphrag, db, neo4j
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI 및 /graphql
│   ├── ingest.py                 # 법률 문서 임베딩 적재 (수동 실행)
│   ├── *.txt                     # 기존 법령 원본 (이전 환경)
│   ├── 판례/                     # 기존 판례 원본 (이전 환경)
│   └── app/
│       ├── database.py
│       ├── graphql/              # schema, resolver, types, inputs
│       ├── models/
│       ├── repositories/         # pgvector 유사도 검색
│       ├── services/             # Agent, Embedding, LLM, compare_service.py
│       └── prompts/              # 법률 응답 정책
├── graphrag_backend/             # GraphRAG FastAPI + Neo4j 검색
│   ├── main.py                   # /api/ask
│   ├── rag.py                    # 그래프 검색 및 LLM 답변
│   ├── embedding.py              # E5 384차원 임베딩
│   ├── graph_db.py               # Cypher / Neo4j
│   ├── parser.py                 # 법률 자료 파싱
│   ├── extractor.py              # 그래프 개체·관계 추출
│   └── ingest.py                 # 수동 적재 (자동 실행 금지)
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── graphql/              # GraphQL 요청
│       ├── pages/                # 상담 화면 및 이력/문서 메뉴
│       ├── components/           # 상담폼/답변/출처 그리드/CompareAnswer.jsx
│       └── styles/
└── nginx/
    ├── Dockerfile               # Vite 빌드 + Nginx
    └── nginx.conf                # 정적 파일 및 리버스 프록시
```

## 🔄 RAG 처리 흐름

```text
사용자 질문 → React → POST /graphql → FastAPI
    → OpenAI 질문 임베딩
    → PostgreSQL(pgvector) 코사인 유사도 TOP 5 검색
    → 검색된 법률 문맥 + 질문 → OpenAI LLM
    → GraphQL 응답(answer, status, sources)
    → React 답변 + AG Grid 출처 + 원문 Modal
```

## 📚 GitHub에서 내려받아 학습 시작하기

이 저장소는 **코드 + 공개 가능한 법률 학습 데이터 + 데이터 출처 정보**를 제공하는 구조를 권장합니다. 다만 현재 패키지에는 실제 법령·판례 원문이 첨부되지 않아 **`data/`에는 안내문과 출처 기록 템플릿만 포함**되어 있습니다. 원문 데이터는 배포 권한 확인 후 별도로 추가해야 합니다.

### 1. 소스 받기

```powershell
git clone https://github.com/lluna93/law_ai_agent_project.git
cd law_ai_agent_project
Copy-Item .env.example .env
```

`.env`에 본인의 OpenAI API 키, DB 접속정보, 기존 볼륨 이름을 입력합니다. `external: true`로 지정된 볼륨은 미리 존재해야 합니다. **신규 학습 환경에서는 기존 볼륨 이름을 임의로 입력하지 말고**, 새 빈 볼륨을 생성한 후 연결하거나 별도 신규 환경용 Compose 설정을 사용하세요.

### 2. 데이터 준비 및 적재

1. `data/README.md`의 출처·공개 조건을 확인하고 허용된 법령·판례 원문만 `data/statutes/`, `data/cases/`에 저장합니다.
2. **현재 적재 스크립트는 기존 `backend/*.txt`, `backend/판례/` 등 경로를 사용할 수 있습니다.** `data/`를 자동으로 읽는다고 가정하지 마세요. 실제 `ingest.py`의 입력 경로를 확인해 데이터 파일을 복사하거나 스크립트 경로를 수정해야 합니다.
3. 빈 PostgreSQL·Neo4j를 준비하고 테이블/인덱스 및 환경변수를 점검합니다.
4. `backend/ingest.py`, `graphrag_backend/ingest.py`를 **각각 수동 실행**합니다. 임베딩 및 개념 추출 과정에서 API 비용이 발생할 수 있습니다.
5. 기존 데이터가 있다면 **재적재하지 말고** 볼륨 연결 상태와 데이터 개수를 확인합니다. 두 적재 스크립트는 자동으로 실행되지 않습니다.

### 3. 실행과 테스트

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

- 프론트엔드: `http://localhost/agent`
- GraphQL: `http://localhost/graphql`
- 테스트 Mutation: 위의 `consultBoth` 예시

> **중요:** 저장소를 `git clone`하는 것만으로 PostgreSQL 임베딩과 Neo4j 지식 그래프가 자동 생성되지는 않습니다. 최초 적재 절차가 필요합니다. 기존 백업을 사용한다면 적재 대신 **각 DB를 별도로 복원**하세요.

## 🚀 Docker 배포

### 1. 기존 DB 볼륨 이름 확인

```powershell
docker volume ls
# 기존 compose 파일이 있다면 볼륨 연결 확인
docker compose config
```

**주의:** 아래 `.env`의 `PGVECTOR_VOLUME_NAME`은 실제 사용 중인 볼륨 이름으로 지정해야 합니다. 볼륨 이름을 잘못 지정하면 기존 데이터가 보이지 않습니다.

### 2. `.env` 구성

```dotenv
POSTGRES_DB=law_rag
POSTGRES_USER=law_user
POSTGRES_PASSWORD=기존_DB_비밀번호
PGVECTOR_VOLUME_NAME=실제_기존_PostgreSQL_볼륨_이름
NEO4J_VOLUME_NAME=실제_기존_Neo4j_볼륨_이름
NEO4J_USER=neo4j
NEO4J_PASSWORD=기존_Neo4j_비밀번호
OPENAI_MODEL=gpt-4.1-mini
DATABASE_URL=postgresql://law_user:URL인코딩된_기존비밀번호@db:5432/law_rag
OPENAI_API_KEY=본인_API_키
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4.1-mini
```

> 이미 초기화된 PostgreSQL 볼륨의 DB 사용자 비밀번호는 `.env` 변경만으로 바뀌지 않습니다. 기존에 사용하던 비밀번호를 사용하세요.

### 3. `docker-compose.yml`의 DB 볼륨 설정

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    volumes:
      - pgvector_data:/var/lib/postgresql/data
    # 기존 서비스의 나머지 설정은 유지

volumes:
  pgvector_data:
    external: true
    name: ${PGVECTOR_VOLUME_NAME}
```

위 예시는 **볼륨 연결에 필요한 부분만** 보여줍니다. 실제 Compose 파일에는 backend, nginx, 네트워크, 환경변수 설정이 함께 있어야 합니다. `external: true`는 지정한 볼륨이 없으면 실행을 실패시키므로, 실수로 빈 DB를 만드는 일을 방지하는 데 유용합니다.

### 4. 빌드 및 실행

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend graphrag
```

### 5. 접속 주소

| 화면/API | URL |
| --- | --- |
| React 메인 | http://localhost |
| AI 상담 | http://localhost/agent |
| GraphQL | http://localhost/graphql |
| 상태 확인 | http://localhost/health |

> 포트 80이 이미 사용 중이면 Compose의 nginx 포트 매핑을 변경하세요.

### 6. GraphQL 헬스 체크

```powershell
$body = @{ query = '{ health }' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost/graphql' -Method Post -ContentType 'application/json' -Body $body
```

## 💾 PostgreSQL·Neo4j 데이터 보존 및 별도 백업

### 원칙

1. PostgreSQL 데이터를 컨테이너 내부가 아닌 **Docker named volume**에 저장합니다.
2. 기존 볼륨을 정확한 이름으로 연결하고, `external: true`로 관리합니다.
3. **`docker compose down -v` 또는 `docker volume rm`을 실행하지 않습니다.**
4. `ingest.py`를 배포 시작 명령에 넣지 않습니다. 기존 데이터를 중복 적재할 수 있습니다.
5. 볼륨 유지와 별개로 **PostgreSQL 논리 백업(`pg_dump`)**을 보관합니다.
6. **Neo4j 데이터는 PostgreSQL dump에 포함되지 않습니다.** 별도로 백업하고, 기존 Neo4j `/data` 볼륨을 두 컨테이너에서 동시에 사용하지 않습니다.

### 기존 데이터 확인

```powershell
docker compose exec db psql -U law_user -d law_rag -c 'SELECT COUNT(*) FROM law_chunks;'
docker volume inspect $env:PGVECTOR_VOLUME_NAME
```

PowerShell에서 `.env` 값은 자동으로 `$env:PGVECTOR_VOLUME_NAME`에 들어가지 않습니다. 환경변수를 별도로 설정하거나 `docker volume inspect 실제_볼륨_이름`으로 실행하세요.

### 백업 (Windows PowerShell)

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
# pg_dump 결과는 컨테이너 안에 생성하고, docker cp로 바이너리 안전하게 복사
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/law_rag.dump'
$cid = docker compose ps -q db
docker cp "${cid}:/tmp/law_rag.dump" .\backups\law_rag.dump
docker compose exec -T db rm -f /tmp/law_rag.dump
```

> **백업 파일은 프로젝트 저장소와 분리해 보관하세요.** `backups/`, `*.dump`, `*.backup`, Neo4j 백업 파일 및 DB 볼륨 아카이브를 `.gitignore`에서 제외하고 GitHub에 업로드하지 않습니다. 암호화된 외장 SSD 또는 접근 제한된 별도 백업 저장소에 보관하세요. PostgreSQL dump에는 Neo4j 그래프가 포함되지 않습니다.

### 다른 PC로 이전

새 PC에서 동일한 PostgreSQL/pgvector 버전의 빈 DB를 준비한 뒤, 백업 파일을 복사하고 `pg_restore`로 복원합니다. **기존 데이터가 있는 DB에는 무작정 복원하지 마세요.** 복원 대상과 충돌 여부를 먼저 확인해야 합니다.

```powershell
$cid = docker compose ps -q db
docker cp .\backups\law_rag.dump "${cid}:/tmp/law_rag.dump"
docker compose exec db pg_restore -U law_user -d law_rag --no-owner /tmp/law_rag.dump
```

> 복원 시 대상 DB는 새로 준비한 빈 데이터베이스여야 하며, `vector` 확장을 설치할 수 있는 권한과 pgvector 이미지가 필요합니다. `pg_restore`에서 충돌이 나면 임의로 `--clean`을 추가하지 말고 대상 DB 상태를 먼저 확인하세요.

### Neo4j 볼륨 연결 예시

```yaml
services:
  neo4j:
    image: neo4j:5.26
    volumes:
      - neo4j_data:/data
volumes:
  neo4j_data:
    external: true
    name: ${NEO4J_VOLUME_NAME}
```

기존 Neo4j 버전 및 실제 볼륨 이름을 확인한 뒤 적용합니다. Neo4j 백업은 PostgreSQL `pg_dump`와 별도 절차로 진행해야 합니다.

## 🔐 보안 및 유의사항

- `.env`, API 키, DB 백업, 개인정보가 포함된 문서를 GitHub에 올리지 않습니다.
- 운영 환경에서는 HTTPS, 인증/인가, 요청 제한, 로그 민감정보 마스킹을 추가해야 합니다.
- 검색된 청크의 출처와 유사도는 법적 정확성의 보증이 아닙니다.
- 공식 판례 원문 연결은 검증된 사건번호 및 URL 메타데이터가 확보된 경우에만 활성화합니다.

## 📄 라이선스 / 데이터 출처 및 공개 기준

- **법령·판결문 원문:** 대한민국 저작권법 제7조의 법령·법원 판결 등은 저작권 보호 대상이 아닌 저작물에 해당할 수 있으나, 개별 자료의 성격과 출처·재이용 조건은 확인해야 합니다.
- **공개 금지 또는 별도 허락 필요 가능:** 민간 판례 해설, 법률 데이터베이스의 편집물, 유료 서비스 수집 데이터, 개인정보·비식별 미흡 자료, 이용약관상 재배포가 제한된 파일.
- **권장 방식:** 공식 출처에서 수집한 허용 자료만 원문 그대로 또는 출처를 명시하여 제공하고, `data/sources.csv`에 URL·수집일·이용조건·검토 결과를 기록합니다. 원문 파일 자체가 공개되지 않은 경우에는 공식 다운로드 링크와 수집 스크립트를 제공하는 방식을 고려하세요.
- **코드와 데이터의 라이선스는 별도**로 관리하며, 공개 배포가 상업적 활용·모델 학습까지 자동 허용한다는 뜻은 아닙니다.

