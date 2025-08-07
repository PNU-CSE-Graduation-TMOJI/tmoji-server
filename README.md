# TMOJI server

# Requires

- python 3.11
- poetry
- docker

# Poetry Package

```
    "fastapi (>=0.116.1,<0.117.0)",
    "uvicorn (>=0.35.0,<0.36.0)",
    "psycopg[binary] (>=3.2.9,<4.0.0)",
    "python-dotenv (>=1.1.1,<2.0.0)"
```

# env & credentials setting

### Google Cloud Credentials

- 구글 번역 API에 필요
- 구글 클라우드에서 받은 인증 키를 아래 경로에 배치
  - `@/credentials/your-gcloud-key.json`

### .env.docker

```bash
ENV_MODE=docker

POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=db
POSTGRES_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0 # 보안상 위험, 변경 예정
CELERY_BROKER_BACKEND=redis://redis:6379/1 # 보안상 위험, 변경 예정

GOOGLE_APPLICATION_CREDENTIALS=/code/credentials/your-gcloud-key.json
# 꼭 `/code/ 접두사를 붙여야 함 (Docker 경로)
```
