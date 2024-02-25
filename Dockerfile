# Stage  1: Build
# Use the latest Python version for the build stage
FROM python:3.12.2-slim as builder

# Create and switch to user
RUN useradd -m app
USER app

# Set environment variables
ENV PATH="/home/app/.local/bin:${PATH}"
WORKDIR /home/app

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache


# Install Poetry
RUN pip install poetry

# Copy pyproject.toml and poetry.lock for dependency resolution
COPY pyproject.toml poetry.lock ./
RUN touch README.md

# Install dependencies
RUN poetry install --only main --no-root && rm -rf $POETRY_CACHE_DIR

# Stage  2: Production
# Use the same base image for the production stage
FROM python:3.12.2-slim as runtime

# Create and switch to user
RUN useradd -m app
USER app

ENV VIRTUAL_ENV=/home/app/.venv \
    PATH="/home/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy application files
COPY ./app ./app
COPY ./templates ./templates
COPY ./static ./static
COPY ./alembic.ini ./
COPY ./alembic ./alembic

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
