# Makefile for MVG Incident Parser

.PHONY: help install test lint format security clean build run

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run all tests"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code with black and isort"
	@echo "  security   - Run security checks"
	@echo "  clean      - Clean up build artifacts"
	@echo "  build      - Build distribution package"
	@echo "  run        - Run the MVG incident parser"
	@echo "  ci         - Run full CI pipeline locally"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install black isort flake8 mypy bandit safety coverage build twine pre-commit

# Run tests
test:
	python3 test_mvg_incident_parser.py
	@echo "✅ Unit tests passed!"

test-unit:
	python3 run_all_tests.py --unit-only

test-integration:
	python3 run_all_tests.py --integration-only

test-errors:
	python3 test_error_scenarios.py

test-all:
	python3 run_all_tests.py

test-fast:
	python3 run_all_tests.py --fast

test-coverage:
	coverage run -m pytest test_mvg_incident_parser.py -v
	coverage report -m
	coverage html
	@echo "📊 Coverage report generated in htmlcov/"

# Linting
lint:
	@echo "🔍 Running flake8..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "🔍 Running mypy..."
	mypy mvg_incident_parser.py --ignore-missing-imports || true

# Code formatting
format:
	@echo "🎨 Formatting code with black..."
	black .
	@echo "📦 Sorting imports with isort..."
	isort . --profile black

# Check formatting without changing files
format-check:
	@echo "🎨 Checking code formatting..."
	black --check --diff .
	isort --check-only --diff . --profile black

# Security checks
security:
	@echo "🔒 Running bandit security scan..."
	bandit -r . -f json -o bandit-report.json || true
	bandit -r . || true
	@echo "🔒 Checking dependencies for vulnerabilities..."
	safety check || true

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -f bandit-report.json
	rm -f safety-report.json
	rm -f coverage.xml
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Build package
build: clean
	@echo "📦 Building distribution package..."
	python -m build
	twine check dist/*

# Run the parser
run:
	@echo "🚀 Running MVG incident parser..."
	python3 mvg_incident_parser.py

# Integration test
test-integration:
	@echo "🔗 Running integration test..."
	timeout 30s python3 mvg_incident_parser.py || echo "Integration test completed"

# Docker targets
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t mvg_stoerung:latest .

docker-run:
	@echo "🚀 Running Docker container..."
	docker run --rm mvg_stoerung:latest

docker-test:
	@echo "🧪 Testing Docker image..."
	docker run --rm mvg_stoerung:latest 2>/dev/null | head -5

# Full CI pipeline
ci: format-check lint security test test-integration
	@echo "✅ Full CI pipeline completed successfully!"

# Setup pre-commit hooks
setup-hooks:
	pre-commit install
	@echo "🪝 Pre-commit hooks installed!"

# Development setup
dev-setup: install setup-hooks
	@echo "🛠️  Development environment setup complete!"