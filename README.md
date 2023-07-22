# Pecuny
Budgeting app written in FastAPI with Jinja2. 
This is my learning project for various subjects:

- Domain Driven Design
- Architecture
- Async
- API Development
- what else there is in a project

## Dev notes

### Starting backend 

Database
`docker compose up --profile dev -d `

FastAPI in docker
`docker run --name=monika --rm -dp 8000:8000 --env-file .env monika`

FastAPI directly
`uvicorn app.main:app` or via VS Code debugger

### Database

Migrate DB with:
`alembic upgrade head`

Create new revision with:
`alembic revision --autogenerate -m "your message"`

### Tests

Use the VS Code Test Module or use the following commands

run all tests with:
`pytest  -v -x -v -s --disable-warnings`

run single test with:
`pytest test_transactions.py::test_update_transaction -v -x -v -s`

