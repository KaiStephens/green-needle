#!/bin/bash
# Green Needle Installation Script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Header
echo "=================================="
echo "Green Needle Installation Script"
echo "=================================="
echo ""

# Check Python version
print_status "Checking Python version..."
if check_command python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_status "Python $PYTHON_VERSION found ✓"
    else
        print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Check FFmpeg
print_status "Checking for FFmpeg..."
if check_command ffmpeg; then
    print_status "FFmpeg found ✓"
else
    print_warning "FFmpeg not found. Installing FFmpeg is recommended for audio processing."
    echo "Install FFmpeg:"
    echo "  - macOS: brew install ffmpeg"
    echo "  - Ubuntu: sudo apt install ffmpeg"
    echo "  - Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Continue without FFmpeg? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing requirements..."
pip install -r requirements.txt

# Install package
print_status "Installing Green Needle..."
pip install -e .

# Check GPU support
print_status "Checking GPU support..."
python3 -c "import torch; gpu = torch.cuda.is_available() or torch.backends.mps.is_available(); print('GPU available ✓' if gpu else 'No GPU detected (CPU mode will be used)')"

# Download a model
echo ""
read -p "Download Whisper base model now? (recommended) (Y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_status "Downloading Whisper base model..."
    python3 -c "import whisper; whisper.load_model('base')"
    print_status "Model downloaded ✓"
fi

# Create directories
print_status "Creating directories..."
mkdir -p output recordings models

# Create example config
if [ ! -f "green-needle.yaml" ]; then
    print_status "Creating example configuration..."
    cat > green-needle.yaml << EOF
# Green Needle Configuration

whisper:
  model: base
  language: null  # auto-detect
  device: auto

audio:
  sample_rate: 16000
  channels: 1

output:
  format: txt
  output_dir: output

processing:
  batch_size: 10
  num_workers: 1
EOF
    print_status "Configuration file created: green-needle.yaml"
fi

# Success message
echo ""
echo "=================================="
echo -e "${GREEN}Installation complete!${NC}"
echo "=================================="
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run Green Needle: green-needle --help"
echo "3. Transcribe audio: green-needle transcribe audio.mp3"
echo ""
echo "For more information, see README.md"