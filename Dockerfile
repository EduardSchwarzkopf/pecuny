# Use the latest Python version
FROM python:3.12.2-slim

# Create and switch to user
RUN useradd -m app
USER app

# Set environment variables
ENV PATH="/home/app/.local/bin:${PATH}"
WORKDIR /home/app

# Install Poetry
COPY ./dist/*.whl ./dist/

RUN pip install ./dist/*.whl

# Copy application files
COPY ./app ./app
COPY ./templates ./templates
COPY ./static ./static
COPY ./alembic.ini ./
COPY ./alembic ./alembic

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
