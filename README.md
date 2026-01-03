### 👉(English README)[./README-EN.md]👈

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

# 폴더 구조

```bash
📁.github ─ 📁workflows : github actions 스크립트 폴더
📁alembic : Database Migration 정보 (Alembic 자동 생성)
📁app ┬ 📁api ─ 📁v1 ┬ 📁endpoints : REST API 작성 폴더
🔸    │               ├ 📁responses : REST API 입출력 예시 (Swagger)
🔸    │               └ 📃routers.py : Router 관리
🔸    ├ 📁constants : 공통적으로 사용되는 상수 관리 폴더
🔸    ├ 📁core : DB Tranjection 훅
🔸    ├ 📁crud : 기본적인 DB Curd 로직 작성 폴더
🔸    ├ 📁models : DATABASE 구조 관리 폴더
🔸    ├ 📁schemas : DATABASE와 매칭되는 Python Type Interface 관리 폴더
🔸    ├ 📁tasks : Celery task 정의 폴더
🔸    ├ 📁utils : 공통적으로 사용되는 유틸 함수 폴더
🔸    ├ 📃__init__.py
🔸    ├ 📃celery_app.py : Celery Core Logic 작성 파일
🔸    ├ 📃db.py : DATABASE Core Logic 작성 파일
🔸    ├ 📃load_env.py : ENV 로드 훅
🔸    └ 📃main.py : 프로젝트 최상위 파일
📁deploy ─ 📁nginx : 실 배포시, Nginx 설정에 필요한 파일
📁docs : 본 문서와 관련된 파일을 담은 폴더
📁font : 이미지 합성 > 기계 번역 때 사용할 폰트
📃.dockerignore : Docker 컨테이너에 복사하지 않을 파일 정의
📃.gitattributes : git 설정 파일
📃.gitignore : commit에서 제외할 파일 규칙 정의
📃alembic.ini : alembic 설정 파일
📃docker-compose.prod.yml : 배포 환경(AWS)에 필요한 Docker Compose 파일
📃docker-compose.yml : 로컬 환경에 필요한 Docker Compose 파일
📃Dockerfile : FastAPI, Celery 컨테이너 구축에 필요한 스크립트 파일
📃poetry.lock : 파이썬 의존성 라이브러리 관리
📃pyproject.ioml : 프로젝트 패키지 관리
📃README.md
```

# Docker Container

본 프로젝트의 Docker Compose 구조는 아래와 같습니다. (🔸: 배포 환경)

### FastAPI_app

- python 3.11 환경의 Image를 이용
- 구성된 FastAPI 프로젝트를 복사하여 필요한 Python 라이브러리 다운로드 후 FastAPI를 가동

### celery_worker

- python 3.11 환경의 Image를 이용
- 구성된 FastAPI 프로젝트를 복사하여 필요한 Python 라이브러리 다운로드 후 celery를 가동
- FastAPI 프로젝트 내부에 구성된 task를 불러와 작업 실행까지 대기

### postgres

- postgres:15 Image를 이용하여 PostgreSQL 가동
- 주입된 환경변수로 PostgreSQL 기본 계정을 구성
- 이후 가동된 FastAPI_app, celery_worker와 통신

### redis

- redis:7 Image를 이용하여 Redis 가동
- 주입된 환경변수로 redis 기본 계정을 구성
- 이후 가동된 celery_worker와 통신

### alembic_migration

- python 3.11 환경의 Image를 이용
- Docker 가동 시 1회 가동 후 종료되며, FastAPI에 정의된 데이터베이스 구조와 실제 PostgreSQL에 구성된 구조와 차이가 생기면 PostgreSQL에 마이그레이션(DBMS 구조 업데이트) 진행

### 🔸nginx_proxy

- nginx:stable-alpine Image를 이용하여 nginx 가동
- 별도의 파일에 설정된 옵션에 따라 SSL 인증, 포트포워딩, 라우팅 등의 기능을 지원

### 🔸certbot

- certbot:certbot Image를 이용하여 certbot 가동
- Docker 가동 시 HTTPS 인증에 필요한 인증서가 없을 때 1회 발급

# Migration

본 프로젝트에서 Migration 도구로 `alembic`을 사용하고 있습니다. Database Model에 변경사항이 생길경우 아래 명령어를 참조하여 migration을 진행해주세요.

```bash
# Docker 이용하지 않을 경우
poetry run alembic upgrade head

# Docker 이용할 경우 (로컬)
docker-compose -f docker-compose.yml --env-file .env run --rm migration

# Docker 이용할 경우 (배포환경, AWS)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env run --rm migration
```

# CI/CD

본 프로젝트는 `.github/workflows/deploy.yml`로 작성된 Github Actions 스크립트로 AWS로의 CI/CD를 구성하였습니다. `prod` branch에 PR Merge로 새로운 내용이 Commit 되면 아래와 같은 작업을 거칩니다.

1. 배포에 필요한 파일 압축 > AWS S3 Bucket에 업로드
2. AWS Credentials를 이용하여 env, gpu 서버 ssh key, gcloud secret key와 같은 환경변수를 주입.
3. AWS EC2에서 S3에 저장된 압축 파일과 Credentials를 불러와 작성된 스크립트를 따라 Docker Container 재가동 진행

# TMOJI 파트별 링크

> 각 파트별 자세한 내용은 아래 Repository에 접속하여 확인할 수 있습니다.

<table>
  <thead>
    <tr>
      <th>분류</th>
      <th>URL</th>
      <th>설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="3">텍스트 변환 모델</td>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/TextCtrl-Translate'>TextCtrl-Translate</a></td>
      <td>한국어 환경에 맞게 파인튜닝된 텍스트 변환 모델</td>
    </tr>
    <tr>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/ko_trocr_tr'>ko-trocr-tr</a></td>
      <td>한국어 환경 TextCtrl에 필요한 한국어 OCR 모델</td>
    </tr>
    <tr>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/SRNet-Datagen_kr'>SRNet-Datagen(ko)</a></td>
      <td>한국어 환경의 TextCtrl 학습에 필요한 데이터셋 Generator</td>
    </tr>
    <tr>
      <td rowspan="2">웹 서비스</td>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/tmoji-web'>웹(FE)</a></td>
      <td>TMOJI 프론트엔드</td>
    </tr>
    <tr>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/tmoji-server'>서버(BE)</a></td>
      <td>TMOJI 백엔드</td>
    </tr>
  </tbody>
</table>
