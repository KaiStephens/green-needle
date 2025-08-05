# Green Needle Makefile

.PHONY: help install install-dev test lint format clean build docker run

# Default target
help:
	@echo "Green Needle - Development Commands"
	@echo "=================================="
	@echo "install      Install package in production mode"
	@echo "install-dev  Install package in development mode"
	@echo "test         Run tests with pytest"
	@echo "lint         Run linters (black, flake8, mypy)"
	@echo "format       Format code with black and isort"
	@echo "clean        Clean build artifacts"
	@echo "build        Build distribution packages"
	@echo "docker       Build Docker image"
	@echo "run          Run green-needle CLI"

# Installation
install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .
	pre-commit install

# Testing
test:
	pytest -v

test-cov:
	pytest -v --cov=green_needle --cov-report=term-missing --cov-report=html

test-fast:
	pytest -v -m "not slow"

# Code quality
lint:
	black --check src/ tests/
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	isort src/ tests/

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Building
build: clean
	python -m build

# Docker
docker:
	docker build -t greenneedle/transcriber:latest .

docker-gpu:
	docker build -t greenneedle/transcriber:gpu --target gpu .

# Running
run:
	green-needle --help

transcribe:
	@echo "Usage: make transcribe FILE=audio.mp3"
	@if [ -z "$(FILE)" ]; then echo "Error: FILE not specified"; exit 1; fi
	green-needle transcribe $(FILE)

record:
	green-needle record --output recording.wav

# Development
dev-server:
	@echo "Starting development server (future feature)..."
	# python -m green_needle.server

# Documentation
docs:
	cd docs && make html

# Release
release-test:
	python -m twine upload --repository testpypi dist/*

release:
	python -m twine upload dist/*