#!/usr/bin/env python3
"""Quick start script to verify Green Needle installation."""

import sys
import os

print("Green Needle Quick Start Test")
print("="*40)

# Test 1: Check Python version
python_version = sys.version_info
print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
if python_version < (3, 8):
    print("⚠️  Warning: Python 3.8+ is recommended")

# Test 2: Try importing the package
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from green_needle import __version__
    print(f"✅ Green Needle version: {__version__}")
except ImportError as e:
    print(f"❌ Failed to import Green Needle: {e}")
    print("   Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Check for FFmpeg
import subprocess
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    print("✅ FFmpeg is installed")
except:
    print("⚠️  FFmpeg not found - audio processing may be limited")

# Test 4: Try importing key components
components = [
    ('Transcriber', 'green_needle.transcriber'),
    ('AudioRecorder', 'green_needle.recorder'),
    ('CLI', 'green_needle.cli'),
    ('Config', 'green_needle.config'),
]

all_good = True
for name, module_path in components:
    try:
        module = __import__(module_path, fromlist=[name.split('.')[-1]])
        print(f"✅ {name} module loaded")
    except ImportError as e:
        print(f"❌ {name} failed: {e}")
        all_good = False

if not all_good:
    print("\n⚠️  Some components failed to load. Missing dependencies?")
    sys.exit(1)

# Test 5: Check for models
print("\nChecking Whisper models...")
try:
    import whisper
    # Check if any models are cached
    import os
    cache_dir = os.path.expanduser("~/.cache/whisper")
    if os.path.exists(cache_dir):
        models = os.listdir(cache_dir)
        if models:
            print(f"✅ Found cached models: {', '.join(models)}")
        else:
            print("📥 No models downloaded yet")
    else:
        print("📥 No models downloaded yet")
except:
    print("❌ Cannot check models - whisper not installed")

# Test 6: Basic functionality test
print("\nTesting basic functionality...")
try:
    from green_needle import Transcriber
    print("✅ Can create Transcriber instance")
    
    # Check if test audio exists
    if os.path.exists('test_audio.wav'):
        print("✅ Test audio file found: test_audio.wav")
        print("\nReady to test transcription!")
        print("Run: green-needle transcribe test_audio.wav")
    else:
        print("ℹ️  No test audio file found")
        print("Run test_core.py to create one")
        
except Exception as e:
    print(f"❌ Functionality test failed: {e}")

print("\n" + "="*40)
print("Quick start test complete!")

if all_good:
    print("\n🎉 Green Needle appears to be properly installed!")
    print("\nNext steps:")
    print("1. Try the CLI: green-needle --help")
    print("2. Record audio: green-needle record --output my_recording.wav")
    print("3. Transcribe: green-needle transcribe test_audio.wav")
else:
    print("\n⚠️  Please install missing dependencies and try again")