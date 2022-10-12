# monika-backend-v2
Monika backend written with fastapi

## Dev notes

### Starting backend 

Database and User-Manager
`docker compose --profile up -d `

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

