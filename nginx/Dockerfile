
# =====================================
# Stage 1. React + Vite 빌드
# =====================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# 의존성 먼저 설치 (Docker 캐시 활용)
COPY frontend/package*.json ./

RUN npm ci

# React 소스 복사
COPY frontend/ ./

# Vite 프로덕션 빌드
RUN npm run build


# =====================================
# Stage 2. Nginx 실행 이미지
# =====================================
FROM nginx:1.27-alpine

# 기본 Nginx 설정 제거
RUN rm /etc/nginx/conf.d/default.conf

# 사용자 정의 설정 복사
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# React 빌드 결과물 복사
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
