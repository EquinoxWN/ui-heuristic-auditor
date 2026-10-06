.PHONY: setup browsers lint test demo bench audit ci

PY ?= python
# Locally the browser lives inside the repo; CI installs it with system dependencies instead.
export PLAYWRIGHT_BROWSERS_PATH ?= $(CURDIR)/.tmp/ms-playwright

setup:
	$(PY) -m pip install --upgrade pip && $(PY) -m pip install -e ".[dev]"

# Download Chromium for Playwright (about 700 MB, into .tmp/ms-playwright).
browsers:
	$(PY) -m playwright install chromium

# ruff, ruff format and mypy --strict.
lint:
	$(PY) -m ruff check . && $(PY) -m ruff format --check . && $(PY) -m mypy

# Real headless Chromium against a local fixture site with seeded accessibility problems.
test:
	$(PY) -m pytest -q

# Audit the seeded fixture page and write report.json and summary.md to .tmp/demo.
demo:
	$(PY) scripts/demo.py

bench:
	@echo "M3: precision and recall on a labeled set of pages with seeded UX problems"

# Known vulnerabilities in the installed Python dependencies.
audit:
	$(PY) -m pip_audit --skip-editable --cache-dir .tmp/pip-audit

ci: setup browsers lint test
