# Multi-stage Dockerfile for Green Needle

# Base stage with common dependencies
FROM python:3.10-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libsndfile1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GREEN_NEEDLE_ENV=development

# Default command for development
CMD ["python", "-m", "green_needle.cli", "--help"]

# Production stage
FROM base as production

# Copy only necessary files
COPY setup.py .
COPY src/ src/
COPY config/ config/

# Install package
RUN pip install .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/output /app/recordings /app/models && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GREEN_NEEDLE_ENV=production
ENV HOME=/app

# Volume for output files
VOLUME ["/app/output", "/app/recordings", "/app/models"]

# Default command
ENTRYPOINT ["green-needle"]
CMD ["--help"]

# GPU support stage (NVIDIA CUDA)
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04 as gpu

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    libsndfile1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy and install package
COPY setup.py .
COPY src/ src/
COPY config/ config/
RUN pip install .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/output /app/recordings /app/models && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV GREEN_NEEDLE_ENV=production
ENV HOME=/app

VOLUME ["/app/output", "/app/recordings", "/app/models"]

ENTRYPOINT ["green-needle"]
CMD ["--help"]