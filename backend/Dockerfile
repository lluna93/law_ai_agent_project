
FROM python:3.13-slim

WORKDIR /app

# Python 실행 환경
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 패키지 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 소스 및 법률 문서 복사
COPY . .

EXPOSE 8000

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
