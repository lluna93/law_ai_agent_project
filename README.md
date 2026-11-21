# ⚖️ Law AI Agent

**React + FastAPI + GraphQL 기반 법률 정보 검색·상담 프로젝트 — RAG(pgvector)와 GraphRAG(Neo4j) 비교**

하나의 법률 질문에 대해 **RAG(문서 유사도 검색)**와 **GraphRAG(벡터 검색 + 법률 지식 관계 확장)**가 독립적으로 답변하도록 설계했습니다. Docker 환경에서 **`consultBoth` GraphQL Mutation 및 React 비교 화면의 실제 실행을 확인**했습니다. 아래에는 기존 RAG 화면과 통합 비교 화면을 모두 수록했습니다.

> ⚠️ 이 프로젝트는 법률 정보 탐색을 위한 데모이며 변호사의 법률 자문을 대체하지 않습니다. 저장된 판례 청크는 판결문 전체가 아닐 수 있으며, 공식 판례 직접 링크는 검증된 사건번호·URL 메타데이터가 있을 때만 제공할 수 있습니다.

## 🏗️ 시스템 아키텍처

![Law AI Agent 시스템 아키텍처](assets/architecture.png)

> 위 아키텍처 이미지는 초기 RAG 중심 설계의 참고 자료입니다. **현재 통합 구조**는 아래의 `consultBoth` 흐름과 GraphRAG 서비스를 함께 확인하세요.

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

## 🆕 RAG + GraphRAG 통합 비교 — 실제 실행 화면

아래 이미지는 **2026-11-21 로컬 Docker 환경에서 실제 실행한 React 화면 캡처**입니다. 동일한 질문을 `consultBoth` Mutation으로 보내 RAG와 GraphRAG 답변을 한 화면에 나란히 표시합니다.

### 1. 질문 입력 및 비교 상담 실행

![RAG GraphRAG 비교 상담 질문 입력](assets/05-compare-question.png)

- 사용자가 입력한 질문: **“AI가 생성한 문구는 저작권이 있나요? (AI가 특정 도서나 논문을 참고시)”**
- **RAG + GraphRAG 비교 상담** 버튼 한 번으로 두 검색 경로를 호출합니다.

### 2. 두 방식의 답변을 나란히 비교

![RAG와 GraphRAG 실제 답변 비교](assets/06-compare-answers.png)

- 왼쪽 **RAG · pgvector**: 검색한 법률 문서 청크를 중심으로 상담 내용 요약, 근거, 대응 방법을 정리합니다.
- 오른쪽 **GraphRAG · Neo4j**: 법률 개념과 연결된 조문·판례 정보를 포함해 근거를 설명합니다.
- 캡처에서 두 응답 모두 `SUCCESS`로 표시됩니다.

### 3. 답변 하단의 검색 출처 TOP 5

![RAG GraphRAG 검색 출처 TOP 5 비교](assets/07-compare-sources.png)

- RAG는 `판례/민법_판례.txt` 등 **문서 청크 출처와 유사도**를 표시합니다.
- GraphRAG는 `대법원:2015다5170` 등 **그래프 검색 출처와 유사도**를 표시합니다.
- 각 항목의 **원문 보기**로 검색에 사용된 내용을 확인할 수 있습니다. 전체 판결문 직접 연결을 의미하지는 않습니다.
- 검색 유사도는 서로 다른 임베딩 모델과 검색 공간에서 계산되므로 **0.44와 0.92를 직접 비교해 어느 쪽이 더 정확하다고 판단할 수 없습니다.**

### 실험 관찰

이번 질문에 대해 개발자는 **GraphRAG의 답변이 더 만족스럽다**고 평가했습니다. 법률 조문·판례를 구조적으로 제시해 근거를 따라가기 쉬웠다는 점이 장점입니다. 다만 이는 **단일 질문에 대한 주관적 관찰**이며, GraphRAG의 법률적 정확도가 더 높다는 검증 결과는 아닙니다.

향후에는 동일 질문 세트에서 **근거 일치율, 판례·조문 인용 정확도, 답변 충실도, 응답 시간, 토큰 비용**을 함께 측정하는 방식으로 비교할 수 있습니다. 화면에 표시된 판례번호와 법률 설명은 LLM 출력이므로 공식 자료를 통한 별도 확인이 필요합니다.

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

## 🖥️ 기존 RAG 실행 화면 (Screenshots)

아래 화면은 Docker로 실행한 **기존 RAG 상담 기능의 실제 브라우저 캡처**입니다. 상담 질문부터 AI 답변, 검색 근거 TOP 5, 저장된 법률 문서 청크 열람까지의 흐름을 보여줍니다.

### 1. AI 법률 상담 입력

![AI 법률 상담 입력 화면](assets/01-consultation-form.png)

- 왼쪽 사이드바: **AI 법률 상담 / 상담 내역 / 법률 자료** 메뉴
- 상단 상태 표시: **GraphQL 연결**
- 상담 질문 입력 및 개인정보 입력 주의 안내
- 화면의 예시 질문: `ai로 만든 글의 저작권`

### 2. AI 법률 상담 결과

![AI 법률 상담 결과](assets/02-ai-answer.png)

- GraphQL `consultLaw` 요청 결과가 `SUCCESS`로 표시됩니다.
- 답변은 상담 내용 요약, 관련 법률 및 근거, 가능한 대응 방법, 추가 확인 사항, 전문가 상담 필요 여부로 구성되어 있습니다.
- **주의:** 화면에 표시된 법률·판례 언급은 LLM 생성 결과입니다. 특정 사건번호나 법률 해석의 정확성이 검증되었다는 의미는 아닙니다.

### 3. RAG 검색 출처 TOP 5

![RAG 검색 출처 TOP 5](assets/03-rag-sources.png)

- **AG Grid**로 순위, 법률 자료 파일명, 코사인 유사도를 표시합니다.
- 캡처에서는 `판례/민법_판례.txt`, `판례/형사소송법_판례.txt`, `판례/대한민국헌법_판례.txt` 등의 파일에서 검색된 청크가 표시됩니다.
- **동일 파일이 여러 번 나타날 수 있습니다.** 문서별 1건이 아니라 *청크 단위 TOP 5*를 검색하기 때문입니다.
- 유사도는 검색 순위를 위한 수치이며 **법적 타당성이나 답변 정확도의 점수는 아닙니다.**

### 4. 검색 원문 상세보기 (Modal)

![검색된 법률 원문 상세보기](assets/04-source-detail-modal.png)

- 검색 결과의 **원문 보기**를 클릭하면 Ant Design Modal이 열립니다.
- 출처 파일명, 검색 유사도, PostgreSQL에 저장된 **실제 검색 청크**를 확인할 수 있습니다.
- **국가법령정보센터에서 판례 검색** 버튼은 공식 검색 페이지를 여는 기능이며, 현재는 선택된 특정 판결문으로 직접 이동하는 링크가 아닙니다.
- 전체 판결문 직접 열람을 위해서는 `case_number`, `official_url`, `document_id` 등 검증된 메타데이터 연결이 추가로 필요합니다.

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
| 컨테이너 배포 | Nginx + FastAPI + PostgreSQL을 Docker Compose로 실행 |

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
├── docker-compose.yml           # nginx, backend, graphrag, db, neo4j
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI 및 /graphql
│   ├── ingest.py                 # 법률 문서 임베딩 적재 (수동 실행)
│   ├── *.txt                     # 법령 원본
│   ├── 판례/                     # 판례 원본
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

## 💾 PostgreSQL·Neo4j 데이터 보존

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

> `backups/`는 `.gitignore`에 추가하고, DB 백업을 공개 GitHub 저장소에 업로드하지 마세요. 판례·법령 원문 등 데이터의 라이선스도 확인해야 합니다.

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

## 📄 라이선스 / 데이터 출처

애플리케이션 코드의 라이선스와 법령·판례 데이터의 이용 조건은 별도로 관리합니다. 법률 문서의 출처, 수집일, 이용 조건을 확인한 후 배포하세요.
