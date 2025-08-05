# Green Needle Makefile

.PHONY: help install install-dev test lint format clean build docker run

# Default target
help:
	@echo "Green Needle - Development Commands"
	@echo "=================================="
	@echo "install      Install package in production mode"
	@echo "install-dev  Install package in development mode"
	@echo "verify       Run basic verification checks"
	@echo "lint         Show linting instructions"
	@echo "format       Show formatting instructions"
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

# Code verification
verify:
	python verify.py

# Code quality (optional - requires dev dependencies)
lint:
	@echo "Linting requires dev dependencies. Run: pip install -r requirements-dev.txt"
	@echo "Then: black --check src/ && flake8 src/"

format:
	@echo "Formatting requires dev dependencies. Run: pip install -r requirements-dev.txt"
	@echo "Then: black src/ && isort src/"

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