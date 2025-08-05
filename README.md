# Green Needle - Audio Transcription System

<div align="center">
  <img src="docs/images/logo.png" alt="Green Needle Logo" width="200" />
  <h3>High-quality local audio transcription using OpenAI Whisper</h3>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
  [![Tests](https://img.shields.io/badge/tests-pytest-orange.svg)](https://pytest.org)
</div>

## 🎯 Overview

Green Needle is a professional-grade audio transcription system designed for long-form content creators, researchers, and anyone who needs to convert hours of spoken audio into text. Built on OpenAI's Whisper model, it provides accurate, local transcription without sending your data to external servers.

### Key Features

- 🎙️ **Long-form Recording Support**: Record and transcribe hours of continuous audio
- 🔒 **100% Local Processing**: Your audio never leaves your machine
- 📝 **Multiple Output Formats**: Plain text, JSON, SRT subtitles, and more
- 🌍 **Multi-language Support**: Transcribe in 99+ languages
- ⚡ **Batch Processing**: Process multiple files efficiently
- 🔧 **Flexible Configuration**: Customize model size, output format, and processing options
- 📊 **Progress Tracking**: Real-time transcription progress with time estimates
- 🐳 **Docker Support**: Easy deployment with containerization

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/green-needle.git
cd green-needle

# Install using pip
pip install -e .

# Or using the installation script
./scripts/install.sh
```

### Basic Usage

```bash
# Transcribe a single audio file
green-needle transcribe audio.mp3

# Record and transcribe
green-needle record --duration 3600 --output transcript.txt

# Batch process multiple files
green-needle batch /path/to/audio/files --output-dir /path/to/transcripts
```

## 📋 Requirements

- Python 3.8 or higher
- FFmpeg (for audio processing)
- 4GB+ RAM (8GB+ recommended for larger models)
- CUDA-capable GPU (optional, for faster processing)

## 🛠️ Installation

### Method 1: Using pip (Recommended)

```bash
pip install green-needle
```

### Method 2: From source

```bash
git clone https://github.com/yourusername/green-needle.git
cd green-needle
pip install -e .
```

### Method 3: Using Docker

```bash
docker pull greenneedle/transcriber:latest
docker run -v /path/to/audio:/audio greenneedle/transcriber transcribe /audio/file.mp3
```

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from [FFmpeg official site](https://ffmpeg.org/download.html)

## 📖 Documentation

### Command Line Interface

```bash
green-needle [command] [options]

Commands:
  transcribe    Transcribe audio file(s)
  record        Record audio and transcribe
  batch         Process multiple files
  config        Manage configuration
  models        List and download Whisper models

Options:
  --model       Whisper model size (tiny, base, small, medium, large)
  --language    Language code (auto-detect if not specified)
  --output      Output file path
  --format      Output format (txt, json, srt, vtt, all)
  --verbose     Enable detailed logging
```

### Configuration

Create a `config.yaml` file:

```yaml
whisper:
  model: base
  language: auto
  device: auto  # cuda, cpu, or auto
  
output:
  format: txt
  timestamps: false
  save_segments: true
  
audio:
  sample_rate: 16000
  channels: 1
  
processing:
  batch_size: 10
  num_workers: 4
```

### Python API

```python
from green_needle import Transcriber

# Initialize transcriber
transcriber = Transcriber(model="base", device="auto")

# Transcribe audio file
result = transcriber.transcribe("audio.mp3")
print(result.text)

# Save in multiple formats
result.save("output.txt", format="txt")
result.save("output.json", format="json")
result.save("output.srt", format="srt")

# Batch processing
results = transcriber.batch_transcribe([
    "audio1.mp3",
    "audio2.wav",
    "audio3.m4a"
])
```

## 🔧 Advanced Usage

### Recording Long Audio Sessions

```python
from green_needle import AudioRecorder, Transcriber

# Record for 2 hours
recorder = AudioRecorder()
audio_file = recorder.record(duration=7200, output="session.wav")

# Transcribe with progress callback
transcriber = Transcriber(model="base")
result = transcriber.transcribe(
    audio_file,
    progress_callback=lambda p: print(f"Progress: {p:.1f}%")
)
```

### Custom Processing Pipeline

```python
from green_needle import Pipeline, processors

# Create custom pipeline
pipeline = Pipeline([
    processors.NoiseReduction(),
    processors.VoiceActivityDetection(),
    processors.WhisperTranscription(model="base"),
    processors.TextPostProcessing(),
    processors.Summarization()  # Optional: summarize long transcripts
])

result = pipeline.process("long_audio.mp3")
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=green_needle

# Run specific test module
pytest tests/test_transcriber.py
```

## 🔍 Model Selection Guide

| Model | Parameters | Required VRAM | Relative Speed | WER |
|-------|------------|---------------|----------------|-----|
| tiny  | 39 M       | ~1 GB         | ~32x           | 17.4% |
| base  | 74 M       | ~1 GB         | ~16x           | 12.6% |
| small | 244 M      | ~2 GB         | ~6x            | 9.5% |
| medium| 769 M      | ~5 GB         | ~2x            | 7.4% |
| large | 1550 M     | ~10 GB        | 1x             | 6.2% |

**Recommendations:**
- **tiny/base**: Good for quick drafts or when accuracy isn't critical
- **small**: Best balance of speed and accuracy for most use cases
- **medium/large**: When maximum accuracy is required

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Fork the repository
# Create your feature branch
git checkout -b feature/amazing-feature

# Commit your changes
git commit -m 'Add amazing feature'

# Push to the branch
git push origin feature/amazing-feature

# Open a Pull Request
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the amazing [Whisper](https://github.com/openai/whisper) model
- The Python community for excellent audio processing libraries
- All contributors who have helped improve this project

## 📞 Support

- 📧 Email: support@greenneedle.io
- 💬 Discord: [Join our community](https://discord.gg/greenneedle)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/green-needle/issues)

## 📈 Roadmap

- [ ] Real-time transcription streaming
- [ ] Speaker diarization
- [ ] Cloud storage integration
- [ ] Web interface
- [ ] Mobile app support
- [ ] API service mode

---

<div align="center">
  Made with ❤️ by the Green Needle Team
</div>