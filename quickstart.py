#!/usr/bin/env python3
"""Quick start script to set up environment and verify Green Needle installation."""

import sys
import os
import subprocess
import platform

print("Green Needle Quick Start")
print("="*50)

# Determine the virtual environment name
VENV_NAME = "venv"
VENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), VENV_NAME)

# Check if virtual environment exists
if not os.path.exists(VENV_PATH):
    print(f"🔧 Creating virtual environment '{VENV_NAME}'...")
    try:
        subprocess.run([sys.executable, "-m", "venv", VENV_PATH], check=True)
        print("✅ Virtual environment created")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        sys.exit(1)
else:
    print(f"✅ Virtual environment '{VENV_NAME}' already exists")

# Determine the pip path based on OS
if platform.system() == "Windows":
    pip_path = os.path.join(VENV_PATH, "Scripts", "pip")
    python_path = os.path.join(VENV_PATH, "Scripts", "python")
else:
    pip_path = os.path.join(VENV_PATH, "bin", "pip")
    python_path = os.path.join(VENV_PATH, "bin", "python")

# Check if dependencies are installed
print("\n📦 Checking dependencies...")
try:
    result = subprocess.run(
        [python_path, "-c", "import whisper; import torch; import click; print('Dependencies OK')"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0 and "Dependencies OK" in result.stdout:
        print("✅ Dependencies already installed")
        deps_installed = True
    else:
        deps_installed = False
except:
    deps_installed = False

if not deps_installed:
    print("📥 Installing dependencies (this may take a few minutes)...")
    print("   Note: This requires ~5GB of free disk space")
    
    # First upgrade pip
    try:
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        print("✅ Pip upgraded")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to upgrade pip: {e}")
    
    # Install requirements
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check disk space: df -h")
        print("2. Try installing manually:")
        print(f"   source {VENV_NAME}/bin/activate  # On Unix/macOS")
        print(f"   {VENV_NAME}\\Scripts\\activate  # On Windows")
        print("   pip install -r requirements.txt")
        sys.exit(1)

# Install the package
print("\n📦 Installing Green Needle...")
try:
    subprocess.run([pip_path, "install", "-e", "."], check=True)
    print("✅ Green Needle installed")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to install Green Needle: {e}")
    sys.exit(1)

# Now run the actual tests
print("\n🧪 Running tests...")
print("="*50)

# Create a test script to run in the virtual environment
test_script = '''
import sys
import os
import subprocess

print(f"Python version: {sys.version}")

# Test 1: Import Green Needle
try:
    from green_needle import __version__
    print(f"✅ Green Needle version: {__version__}")
except ImportError as e:
    print(f"❌ Failed to import Green Needle: {e}")
    sys.exit(1)

# Test 2: Check for FFmpeg
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    print("✅ FFmpeg is installed")
except:
    print("⚠️  FFmpeg not found - audio processing may be limited")
    print("   Install: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")

# Test 3: Import key components
try:
    from green_needle import Transcriber, AudioRecorder, Pipeline, BatchProcessor
    print("✅ All core components loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import components: {e}")

# Test 4: Check for models
print("\\n📊 Checking Whisper models...")
try:
    import whisper
    import torch
    
    print(f"✅ Whisper is available")
    print(f"✅ PyTorch is available (device: {'cuda' if torch.cuda.is_available() else 'cpu'})")
    
    # Check cached models
    cache_dir = os.path.expanduser("~/.cache/whisper")
    if os.path.exists(cache_dir):
        models = [f for f in os.listdir(cache_dir) if f.endswith('.pt')]
        if models:
            print(f"✅ Found cached models: {', '.join(models)}")
        else:
            print("📥 No models downloaded yet (will download on first use)")
    else:
        print("📥 No models downloaded yet (will download on first use)")
except Exception as e:
    print(f"❌ Error checking models: {e}")

# Test 5: CLI availability
print("\\n🖥️  Testing CLI...")
try:
    result = subprocess.run(['green-needle', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ CLI is working: {result.stdout.strip()}")
    else:
        print("⚠️  CLI not in PATH, use: python -m green_needle.cli")
except:
    print("⚠️  CLI not in PATH, use: python -m green_needle.cli")

# Test 6: Check for test audio
print("\\n🎵 Checking test audio...")
if os.path.exists('test_audio.wav'):
    print("✅ Test audio file found: test_audio.wav")
    print("\\n🚀 Ready to test transcription!")
    print("   Try: green-needle transcribe test_audio.wav --model tiny")
    print("   Or:  python -m green_needle.cli transcribe test_audio.wav --model tiny")
else:
    print("ℹ️  No test audio file found")
    print("   Record one: green-needle record --duration 5 --output test_audio.wav")

print("\\n" + "="*50)
print("✅ Setup complete! Green Needle is ready to use.")
print("\\n📚 Quick commands:")
print("1. Activate environment:")
print(f"   source {os.path.basename(sys.prefix)}/bin/activate  # Unix/macOS")
print(f"   {os.path.basename(sys.prefix)}\\\\Scripts\\\\activate  # Windows")
print("2. Transcribe audio:")
print("   green-needle transcribe audio.mp3")
print("3. Record audio:")
print("   green-needle record --output recording.wav")
print("4. Get help:")
print("   green-needle --help")
'''

# Write the test script to a temporary file
with open('.quickstart_test.py', 'w') as f:
    f.write(test_script)

# Run the test script in the virtual environment
try:
    subprocess.run([python_path, '.quickstart_test.py'], check=True)
except subprocess.CalledProcessError:
    pass  # Error already printed by the script
finally:
    # Clean up
    if os.path.exists('.quickstart_test.py'):
        os.remove('.quickstart_test.py')

print(f"\n💡 To use Green Needle, activate the virtual environment:")
if platform.system() == "Windows":
    print(f"   {VENV_NAME}\\Scripts\\activate")
else:
    print(f"   source {VENV_NAME}/bin/activate")