# The same four gates CI runs. `make install` once, then `make check`.
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: install check lint format typecheck test

install:
	python3 -m venv $(VENV)
	$(BIN)/pip install -e ".[dev]"

check: lint format typecheck test

lint:
	$(BIN)/ruff check .

format:
	$(BIN)/ruff format --check .

typecheck:
	$(BIN)/mypy

test:
	$(BIN)/pytest
