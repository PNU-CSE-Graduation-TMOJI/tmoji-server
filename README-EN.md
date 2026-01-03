[![banner](/docs/banner.png)](https://tmoji.org)

# TMOJI SERVER (Backend)

> An image translation service that preserves original font styles

### [TMOJI SERVER API Documentation](https://api.tmoji.org/docs)

#### [TMOJI Website](https://tmoji.org)
- This repository contains the backend server implementation for TMOJI, an image translation service that preserves original font styles.

# Requirements
- python 3.11
- poetry
- docker
- docker-compose

# Running with Docker Compose

This project is fully containerized using Docker.
By running it with Docker Compose, you can start the entire system without installing additional libraries or databases locally.

```bash
# For Local Environment
docker-compose -f docker-compose.yml --env-file .env up -d --build

# For Production Environment (AWS EC2)
docker compose --env-file .env.docker \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build

```

# Poetry

- Required dependencies are automatically installed based on `pyproject.toml`.

If you are **not using Docker**, install dependencies with the following command:

```bash
poetry install --no-root
```

# Environment & Credential Setup

### Google Cloud Credentials

- Required for **Google Translation API**
- Place the Google Cloud service account key at the following path:
  - `@/credentials/your-gcloud-key.json`

### SSH Secret Key

- The **TextCtrl model server is separated** and accessed via SSH
- SSH key files must be stored separately:
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

# Must include `/code/` prefix (Docker path)
GOOGLE_APPLICATION_CREDENTIALS=/code/credentials/your-gcloud-key.json

# SSH configuration for TextCtrl model server (all values are confidential)
GPU_KEY_PATH=/run/secrets/your_secret_ssh_key_file_name
GPU_HOST=your_gpu_server_host
GPU_PORT=your_gpu_server_ssh_port
GPU_USER=your_gpu_server_user
GPU_REMOTE_IN=secret
GPU_REMOTE_OUT=secret
GPU_REMOTE_SCRIPT=secret
GPU_REMOTE_PREAMBLE=secret

```

# Project Structure

```bash
📁 .github/workflows       # GitHub Actions scripts
📁 alembic                 # Database migration files (auto-generated)
📁 app
 ├ 📁 api/v1/endpoints     # REST API endpoints
 ├ 📁 responses            # Swagger API I/O examples
 ├ 📄 routers.py           # API router management
 ├ 📁 constants            # Shared constants
 ├ 📁 core                 # DB transaction hooks
 ├ 📁 crud                 # Basic CRUD logic
 ├ 📁 models               # Database schema definitions
 ├ 📁 schemas              # Pydantic schemas
 ├ 📁 tasks                # Celery task definitions
 ├ 📁 utils                # Shared utility functions
 ├ 📄 celery_app.py        # Celery core logic
 ├ 📄 db.py                # Database core logic
 ├ 📄 load_env.py          # Environment loader
 └ 📄 main.py              # Application entry point
📁 deploy/nginx             # Nginx configuration for production
📁 docs                     # Documentation assets
📁 font                     # Fonts used for image synthesis and translation
📄 .dockerignore
📄 .gitattributes
📄 .gitignore
📄 alembic.ini
📄 docker-compose.prod.yml  # Production Docker Compose (AWS)
📄 docker-compose.yml       # Local Docker Compose
📄 Dockerfile               # FastAPI & Celery container build file
📄 poetry.lock
📄 pyproject.toml
📄 README.md

```

# Docker Container

The Docker Compose architecture consists of the following services
(🔸 = production only):

### FastAPI_app

- Runs on Python 3.11
- Hosts the FastAPI application
- Installs required dependencies and starts the API server

### celery_worker

- Runs on Python 3.11
- Executes asynchronous tasks defined in the FastAPI project
- Waits for and processes tasks via Celery

### postgres

- Uses postgres:15
- Initializes PostgreSQL with environment variables
- Communicates with FastAPI and Celery

### redis

- Uses redis:7
- Acts as the message broker for Celery

### alembic_migration

- Runs once on container startup
- Applies database migrations if schema differences are detected

### 🔸nginx_proxy

- Uses nginx:stable-alpine
- Handles SSL, port forwarding, and routing

### 🔸certbot

- Uses certbot/certbot
- Automatically issues HTTPS certificates if not already present

# Database Migration

This project uses Alembic for database migrations.

```bash
# Without Docker
poetry run alembic upgrade head

# With Docker (local)
docker-compose -f docker-compose.yml --env-file .env run --rm migration

# With Docker (production / AWS)
docker-compose -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env \
  run --rm migration

```

# CI/CD

CI/CD is implemented using **GitHub Actions** (`.github/workflows/deploy.yml`).
When a pull request is merged into the `prod` branch, the following steps are executed:

1. Compress deployment files and upload them to an AWS S3 bucket
2. Inject environment variables and secrets (env files, GPU server SSH keys, Google Cloud credentials)
3. On AWS EC2, download artifacts from S3 and restart Docker containers according to deployment scripts

# TMOJI Related Repositories

> Detailed implementations for each component can be found in the repositories below.

<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Repository</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="3">Text Transformation Models</td>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/TextCtrl-Translate'>TextCtrl-Translate</a></td>
      <td>Fine-tuned text transformation model optimized for Korean</td>
    </tr>
    <tr>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/ko_trocr_tr'>ko-trocr-tr</a></td>
      <td>Korean OCR model required for TextCtrl</td>
    </tr>
    <tr>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/SRNet-Datagen_kr'>SRNet-Datagen (ko)</a></td>
      <td>Dataset generator for TextCtrl training</td>
    </tr>
    <tr>
      <td rowspan="2">Web Services</td>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/tmoji-web'>TMOJI Web (Frontend)</a></td>
      <td>TMOJI frontend</td>
    </tr>
    <tr>
      <td><a href='https://github.com/PNU-CSE-Graduation-TMOJI/tmoji-server'>TMOJI Server (Backend)</a></td>
      <td>TMOJI backend</td>
    </tr>
  </tbody>
</table>
