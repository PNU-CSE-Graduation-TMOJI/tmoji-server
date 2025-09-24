[![banner](/docs/banner.png)](https://tmoji.org)

# TMOJI SERVER (BE)

> 폰트 스타일을 유지하며 이미지를 번역하는 서비스

### [TMOJI SERVER API 명세서 바로가기](https://api.tmoji.org/docs)

#### [TMOJI 웹 사이트 바로가기](https://tmoji.org)

- 이미지 번역 서비스 TMOJI의 SERVER 파트 레포지토리입니다.

# Requires

- python 3.11
- poetry
- docker
- docker-compose

# Run Docker Compose

본 프로젝트는 Docker로 Container화 되어있습니다. Docker Compose로 실행한다면 별도의 라이브러리, Database 설치 필요 없이 프로젝트를 가동할 수 있습니다. 아래 명령어를 참고해 주세요.

```bash
# For Local Env
docker-compose -f docker-compose.yml --env-file .env up -d --build

# For Production Env (In Aws EC2)
docker compose --env-file .env.docker -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

# Poetry

- 필요한 dependencies는 pyproject.toml에 명시된 라이브러리들에 의해 자동으로 설치 됩니다.

아래 명령어를 참고하여 라이브러리를 설치해주세요. (Docker를 이용한다면 설치할 필요 없습니다.)

```bash
poetry install --no-root
```

# env & credentials setting

### Google Cloud Credentials

- 구글 번역 API에 필요
- 구글 클라우드에서 받은 인증 키를 아래 경로에 배치
  - `@/credentials/your-gcloud-key.json`

### SSH Secret Key

- TextCtrl 모델 서버가 분리되어있어 SSH 연결 수행
- SSH 연결 관련 Secret Key 파일을 따로 저장하여야함.
  - `@/secrets/OPEN_SSH_PRIVATE_KEY`
  - `@/secrets/OPEN_SSH_PUB_FILE.pub`

### Environment Variables

```bash
# env (local)

ENV_MODE=docker

POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=db
POSTGRES_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_BROKER_BACKEND=redis://redis:6379/1

# 꼭 `/code/ 접두사를 붙여야 함 (Docker 경로)
GOOGLE_APPLICATION_CREDENTIALS=/code/credentials/your-gcloud-key.json

# TextCtrl 모델 서버와 SSH 통신을 위해 작성
# 보안상 모두 비공개
GPU_KEY_PATH=/run/secrets/your_secret_ssh_key_file_name
GPU_HOST=your_gpu_server_host
GPU_PORT=your_gpu_server_ssh_port
GPU_USER=your_gpu_server_user
GPU_REMOTE_IN=secret
GPU_REMOTE_OUT=secret
GPU_REMOTE_SCRIPT=secret
GPU_REMOTE_PREAMBLE=secret
```
