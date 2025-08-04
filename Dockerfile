FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /code

# Install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

# Copy only poetry files to cache dependencies
COPY pyproject.toml poetry.lock* README.md /code/

# Install dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-root --no-interaction --no-ansi

# Copy source code
COPY . /code
