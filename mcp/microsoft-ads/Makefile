# The same four gates CI runs. `make install` once, then `make check`.
VENV ?= .venv
BIN := $(VENV)/bin
SDIST := .cache/msads.tar.gz

.PHONY: install check lint format typecheck test catalog

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

# Regenerate src/microsoft_ads_mcp/catalog.json from the pinned msads sdist on PyPI. The
# builder refuses the download unless its sha256 matches the pin in catalog_build.py.
catalog:
	mkdir -p .cache
	$(BIN)/python -c "from microsoft_ads_mcp.catalog_build import SDIST_URL; print(SDIST_URL)" \
		| xargs curl -fsSL -o $(SDIST)
	$(BIN)/microsoft-ads-build-catalog $(SDIST) src/microsoft_ads_mcp
