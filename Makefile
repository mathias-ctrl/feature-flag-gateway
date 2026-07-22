.PHONY: install test lint format run migrate up

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .
	mypy app

format:
	ruff format .
	ruff check --fix .

run:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head

up:
	docker compose up --build
