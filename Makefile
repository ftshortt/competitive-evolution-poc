PYTHON=python3
PACKAGE=evoagent
.PHONY: fmt lint test run up down
fmt:
	black src tests
	ruff check --fix src tests
lint:
	ruff check src tests
test:
	pytest -q --cov=src --cov-report=term-missing
run:
	$(PYTHON) -m src.evoagent
up:
	docker compose up -d --build
down:
	docker compose down
