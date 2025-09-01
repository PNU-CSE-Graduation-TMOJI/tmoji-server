# TMOJI server

## Requires

- python 3.11
- poetry
- docker

## Poetry

- 필요한 dependencies는 pyproject.toml에 명시된 라이브러리들에 의해 자동으로 설치 됨

## env & credentials setting

### Google Cloud Credentials

- 구글 번역 API에 필요
- 구글 클라우드에서 받은 인증 키를 아래 경로에 배치
  - `@/credentials/your-gcloud-key.json`

### AWS credentilas (로컬에서 s3 접근 시 필요)

PowerShell에서 한 번만 설정:

```sh
aws configure --profile tmoji
# AWS Access Key ID: <발급받은 키>
# AWS Secret Access Key: <발급받은 시크릿>
# Default region name: <region>
# Default output format: json
```

확인:

```sh
aws sts get-caller-identity --profile tmoji
aws s3 ls s3://your-bucket-name --profile tmoji
```

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

## 도커 가동

### Local

```bash
docker-compose -f docker-compose.yml --env-file .env up -d --build
```
