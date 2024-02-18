# Use the latest Python version
FROM python:3.12.2-bookworm

# Create and switch to user
RUN useradd -m app
USER app

# Set environment variables
ENV PATH="/home/app/.local/bin:${PATH}"
WORKDIR /home/app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock ./

# Install dependencies with Poetry
RUN poetry install --no-interaction --no-cache

# Copy application files
COPY ./app ./app
COPY ./templates ./templates
COPY ./static ./static
COPY ./alembic.ini ./
COPY ./alembic ./alembic

# Run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
