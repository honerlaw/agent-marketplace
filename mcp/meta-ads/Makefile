# The same four gates CI runs. `make install` once, then `make check`.
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: install check lint format typecheck test specs

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

# Meta's endpoint specs for local use: then set META_ADS_SPEC_PATH=$(CURDIR)/specs.
specs:
	$(BIN)/meta-ads-fetch-specs specs
