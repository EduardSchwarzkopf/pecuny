# Pecuny
Budgeting app written in FastAPI with Jinja2. 
This is my learning project for various subjects:

- Domain Driven Design
- Architecture
- Async
- API Development
- what else there is in a project

## Dev notes

### Prerequisites

1. [poetry](https://python-poetry.org/docs/) installed
2. python ^3.12 installed

### Install packages

Use `poetry` to install packages: `poetry install`

### VSCode Setup

Set the correct env in VS Code with: 

1. Get the env path with: `poetry env info --path`
2. `Ctrl` + `P`
2. Search for `Python interpreter`
3. Set the path from step 1

### Starting backend 

Database
`docker compose up --profile dev -d `

FastAPI in docker
`docker run --name=monika --rm -dp 8000:8000 --env-file .env monika`

FastAPI directly
`uvicorn app.main:app` or via VS Code debugger

### Database

Migrate DB with:
`poetry run alembic upgrade head`

Create new revision with:
`poetry run alembic revision --autogenerate -m "your message"`

### Tests

Use the VS Code Test Module or use the following commands

run all tests with:
`poetry run pytest  -v -x -v -s --disable-warnings`

run single test with:
`poetry run pytest test_transactions.py::test_update_transaction -v -x -v -s`

