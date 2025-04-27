# -*- makefile -*-
# Arsla Programming Language Build System

.PHONY: all install uninstall test format lint mypy docs clean clean-all run-examples bump-major bump-minor bump-patch

# Config
VENV_NAME?=venv
VENV_BIN=$(VENV_NAME)/bin
PYTHON=$(VENV_BIN)/python3
PIP=$(VENV_BIN)/pip
PYTEST=$(VENV_BIN)/pytest
SPHINX_BUILD=$(VENV_BIN)/sphinx-build
VERSION_FILE=src/mygolf/__init__.py

# Help
all: help
help:
	@echo "Arsla Build System"
	@echo
	@echo "Commands:"
	@echo "  install         Create venv and install dev dependencies"
	@echo "  test            Run tests with coverage"
	@echo "  format          Auto-format code with Black"
	@echo "  lint            Lint code with Ruff"
	@echo "  mypy            Static type checking"
	@echo "  docs            Build documentation"
	@echo "  clean           Remove build artifacts"
	@echo "  clean-all       Remove all generated files (including venv)"
	@echo "  run-examples    Execute example programs"
	@echo "  bump-major      Bump major version (X.0.0)"
	@echo "  bump-minor      Bump minor version (0.X.0)"
	@echo "  bump-patch      Bump patch version (0.0.X)"
	@echo

# Core
install:
	python3 -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip wheel
	$(PIP) install -e .[dev]
	@echo "\n✅ Virtual environment ready. Activate with: source $(VENV_BIN)/activate"

uninstall:
	rm -rf $(VENV_NAME)
	$(PYTHON) -m pip uninstall -y arsla-lang

test:
	$(PYTEST) -v --cov=src --cov-report=term-missing --cov-report=html:coverage_report tests/

# Code Quality
format:
	$(VENV_BIN)/black src tests
	$(VENV_BIN)/ruff --fix src tests

lint:
	$(VENV_BIN)/ruff check src tests
	$(VENV_BIN)/black --check src tests

mypy:
	$(VENV_BIN)/mypy src

# Documentation
docs:
	$(SPHINX_BUILD) -b html docs/source docs/build
	@echo "\n📚 Documentation built at docs/build/index.html"

# Packaging
dist: clean
	$(PYTHON) -m build
	$(VENV_BIN)/twine check dist/*

publish: dist
	$(VENV_BIN)/twine upload dist/*

# Versioning
bump-major:
	$(VENV_BIN)/bumpver update --major

bump-minor:
	$(VENV_BIN)/bumpver update --minor

bump-patch:
	$(VENV_BIN)/bumpver update --patch

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info .coverage coverage_report/ .mypy_cache/ .pytest_cache/

clean-all: clean
	rm -rf $(VENV_NAME) docs/build/ .DS_Store __pycache__

# Examples
run-examples:
	@for example in examples/*.golf; do \
		echo "\n🏃 Running $${example}..."; \
		$(PYTHON) -m mygolf.cli $${example}; \
	done
