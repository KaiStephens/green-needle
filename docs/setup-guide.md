# Green Needle Setup Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [GPU Setup](#gpu-setup)
4. [Troubleshooting](#troubleshooting)
5. [Performance Optimization](#performance-optimization)

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8 or higher
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **CPU**: x86_64 processor

### Recommended Requirements
- **RAM**: 16GB or more
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional)
- **Storage**: 10GB free space (for models)
- **Network**: Broadband for model downloads

### Software Dependencies
- FFmpeg (for audio processing)
- Git (for installation from source)

## Installation Methods

### Method 1: Quick Install (pip)

```bash
# Install from PyPI (when published)
pip install green-needle

# Install from GitHub
pip install git+https://github.com/yourusername/green-needle.git
```

### Method 2: From Source (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/yourusername/green-needle.git
cd green-needle

# Run installation script
# macOS/Linux:
./scripts/install.sh

# Windows:
scripts\install.bat
```

### Method 3: Manual Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

### Method 4: Docker

```bash
# Pull pre-built image
docker pull greenneedle/transcriber:latest

# Or build from source
docker build -t greenneedle/transcriber .
```

## Platform-Specific Setup

### macOS

1. **Install Homebrew** (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install FFmpeg**:
   ```bash
   brew install ffmpeg
   ```

3. **Install PortAudio** (for recording):
   ```bash
   brew install portaudio
   ```

### Ubuntu/Debian

1. **Update package list**:
   ```bash
   sudo apt update
   ```

2. **Install dependencies**:
   ```bash
   sudo apt install python3-pip python3-venv ffmpeg libsndfile1 portaudio19-dev
   ```

### Windows

1. **Install Python** from [python.org](https://python.org)
   - Check "Add Python to PATH" during installation

2. **Install FFmpeg**:
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to System PATH

3. **Install Visual C++ Build Tools** (if needed):
   - Download from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

## GPU Setup

### NVIDIA GPU (CUDA)

1. **Check GPU compatibility**:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.get_device_name(0))
   ```

2. **Install CUDA Toolkit** (if not using Docker):
   - Download from [NVIDIA](https://developer.nvidia.com/cuda-downloads)
   - Version 11.8 or higher recommended

3. **Install PyTorch with CUDA**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### Apple Silicon (M1/M2)

Green Needle automatically detects and uses Metal Performance Shaders (MPS):

```python
import torch
print(torch.backends.mps.is_available())
```

No additional setup required!

## Verification

### 1. Verify Installation

```bash
# Check CLI
green-needle --version

# Test transcription
green-needle transcribe --help
```

### 2. Verify Python API

```python
from green_needle import Transcriber

# Should not raise any errors
transcriber = Transcriber(model="tiny")
print("Installation successful!")
```

### 3. Run System Check

```bash
# Run built-in system check
python -m green_needle.check_system
```

## Model Management

### Download Models

Models are downloaded automatically on first use, or manually:

```bash
# Download specific model
green-needle models --download base

# List available models
green-needle models --list
```

### Model Storage Locations

- **Default**: `~/.cache/whisper/`
- **Custom**: Set `WHISPER_CACHE_DIR` environment variable

## Configuration

### 1. Create Configuration File

```bash
# Generate default config
green-needle config --generate > green-needle.yaml
```

### 2. Environment Variables

```bash
# Set default model
export GREEN_NEEDLE_MODEL=base

# Set device
export GREEN_NEEDLE_DEVICE=cuda

# Set output directory
export GREEN_NEEDLE_OUTPUT_DIR=/path/to/output
```

### 3. User Config Location

- **macOS/Linux**: `~/.config/green-needle/config.yaml`
- **Windows**: `%APPDATA%\green-needle\config.yaml`

## Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
```bash
# Error: ffmpeg not found

# Solution - Install FFmpeg:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download and add to PATH
```

#### 2. No Module Named 'whisper'
```bash
# Error: ModuleNotFoundError: No module named 'whisper'

# Solution:
pip install --upgrade openai-whisper
```

#### 3. CUDA Out of Memory
```python
# Error: CUDA out of memory

# Solution 1: Use smaller model
transcriber = Transcriber(model="tiny")

# Solution 2: Use CPU
transcriber = Transcriber(device="cpu")
```

#### 4. Audio Device Not Found
```python
# Error: No audio input device found

# Solution: List and select device
from green_needle import AudioRecorder
devices = AudioRecorder.list_devices()
recorder = AudioRecorder(device=devices[0]['index'])
```

### Debug Mode

Enable debug logging:

```bash
# CLI
green-needle --verbose transcribe audio.mp3

# Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### 1. Model Selection

| Use Case | Recommended Model | Device |
|----------|------------------|---------|
| Quick drafts | tiny | CPU |
| General use | base | CPU/GPU |
| High accuracy | small/medium | GPU |
| Best quality | large | GPU |

### 2. GPU Acceleration

```python
# Force GPU usage
transcriber = Transcriber(model="base", device="cuda")

# Check GPU memory usage
import torch
print(f"GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")
```

### 3. Batch Processing

```bash
# Use multiple workers for batch processing
green-needle batch /audio/dir --num-workers 4 --output-dir /output
```

### 4. Memory Management

```python
# Process large files in chunks
from green_needle.utils import split_audio_file

chunks = split_audio_file("long_audio.mp3", chunk_duration=1800)
for chunk in chunks:
    result = transcriber.transcribe(chunk)
```

## Next Steps

1. Read the [Examples](examples.md) for usage patterns
2. Check the [API Reference](api-reference.md) for detailed documentation
3. Join our [Discord](https://discord.gg/greenneedle) for support
4. Report issues on [GitHub](https://github.com/yourusername/green-needle/issues)