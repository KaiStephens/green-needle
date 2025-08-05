@echo off
REM Green Needle Installation Script for Windows

echo ==================================
echo Green Needle Installation Script
echo ==================================
echo.

REM Check Python version
echo [INFO] Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.8 or higher is required
    pause
    exit /b 1
)

echo [INFO] Python version OK
echo.

REM Check FFmpeg
echo [INFO] Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg not found. Installing FFmpeg is recommended.
    echo Download from: https://ffmpeg.org/download.html
    echo.
    set /p CONTINUE="Continue without FFmpeg? (y/N): "
    if /i not "%CONTINUE%"=="y" exit /b 1
) else (
    echo [INFO] FFmpeg found
)
echo.

REM Create virtual environment
echo [INFO] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo [INFO] Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements
    pause
    exit /b 1
)

REM Install package
echo [INFO] Installing Green Needle...
pip install -e .
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Green Needle
    pause
    exit /b 1
)

REM Check GPU support
echo.
echo [INFO] Checking GPU support...
python -c "import torch; gpu = torch.cuda.is_available(); print('GPU available' if gpu else 'No GPU detected (CPU mode will be used)')"

REM Download model
echo.
set /p DOWNLOAD="Download Whisper base model now? (recommended) (Y/n): "
if /i not "%DOWNLOAD%"=="n" (
    echo [INFO] Downloading Whisper base model...
    python -c "import whisper; whisper.load_model('base')"
    echo [INFO] Model downloaded
)

REM Create directories
echo [INFO] Creating directories...
if not exist output mkdir output
if not exist recordings mkdir recordings
if not exist models mkdir models

REM Create example config
if not exist green-needle.yaml (
    echo [INFO] Creating example configuration...
    (
        echo # Green Needle Configuration
        echo.
        echo whisper:
        echo   model: base
        echo   language: null  # auto-detect
        echo   device: auto
        echo.
        echo audio:
        echo   sample_rate: 16000
        echo   channels: 1
        echo.
        echo output:
        echo   format: txt
        echo   output_dir: output
        echo.
        echo processing:
        echo   batch_size: 10
        echo   num_workers: 1
    ) > green-needle.yaml
    echo [INFO] Configuration file created: green-needle.yaml
)

REM Success
echo.
echo ==================================
echo Installation complete!
echo ==================================
echo.
echo To get started:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run Green Needle: green-needle --help
echo 3. Transcribe audio: green-needle transcribe audio.mp3
echo.
echo For more information, see README.md
echo.
pause