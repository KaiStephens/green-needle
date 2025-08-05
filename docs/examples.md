# Green Needle Examples

## Basic Usage

### 1. Simple Transcription

Transcribe a single audio file:

```bash
green-needle transcribe audio.mp3
```

### 2. Specify Output Format

```bash
green-needle transcribe audio.mp3 --format json --output transcript.json
```

### 3. Use Different Model

```bash
# Use larger model for better accuracy
green-needle transcribe audio.mp3 --model large

# Use smaller model for faster processing
green-needle transcribe audio.mp3 --model tiny
```

### 4. Specify Language

```bash
# Force English transcription
green-needle transcribe audio.mp3 --language en

# Spanish transcription
green-needle transcribe audio.mp3 --language es
```

## Recording Audio

### 1. Record for Specific Duration

```bash
# Record for 30 minutes
green-needle record --duration 1800 --output recording.wav
```

### 2. Interactive Recording

```bash
# Record until user presses Enter
green-needle record --output session.wav
```

### 3. Record and Transcribe

```bash
green-needle record --output lecture.wav --transcribe --model base
```

## Batch Processing

### 1. Process Directory

```bash
green-needle batch /path/to/audio/files --output-dir /path/to/transcripts
```

### 2. Process Specific File Types

```bash
green-needle batch ./podcasts --pattern "*.mp3" --output-dir ./transcripts
```

### 3. Recursive Processing

```bash
green-needle batch ./media --recursive --output-dir ./output
```

## Python API Examples

### 1. Basic Transcription

```python
from green_needle import Transcriber

# Initialize transcriber
transcriber = Transcriber(model="base")

# Transcribe audio
result = transcriber.transcribe("meeting.mp3")

# Print transcript
print(result.text)

# Save in different formats
result.save("meeting.txt", format="txt")
result.save("meeting.srt", format="srt")
```

### 2. Language Detection

```python
from green_needle import Transcriber

transcriber = Transcriber()

# Detect language
languages = transcriber.detect_language("international_call.mp3")

# Get most likely language
top_language = max(languages, key=languages.get)
print(f"Detected language: {top_language} ({languages[top_language]:.1%})")
```

### 3. Progress Tracking

```python
from green_needle import Transcriber
from tqdm import tqdm

transcriber = Transcriber(model="base")

# Create progress bar
pbar = tqdm(total=100, desc="Transcribing")

def update_progress(progress):
    pbar.n = progress
    pbar.refresh()

# Transcribe with progress
result = transcriber.transcribe(
    "long_audio.mp3",
    progress_callback=update_progress
)

pbar.close()
```

### 4. Batch Processing with Python

```python
from green_needle import BatchProcessor
from pathlib import Path

# Initialize batch processor
processor = BatchProcessor(
    model="base",
    output_format="json",
    num_workers=4
)

# Find audio files
audio_files = list(Path("./interviews").glob("*.wav"))

# Process files
results = processor.process_files(
    audio_files,
    output_dir="./transcripts",
    skip_existing=True
)

# Generate report
report = processor.generate_report(results)
print(report)
```

### 5. Custom Pipeline

```python
from green_needle import Pipeline, processors

# Create custom pipeline
pipeline = Pipeline([
    processors.AudioLoader(sample_rate=16000),
    processors.NoiseReduction(prop_decrease=0.8),
    processors.VoiceActivityDetection(aggressiveness=2),
    processors.WhisperTranscription(model="base"),
    processors.TextPostProcessing(remove_filler_words=True),
    processors.Summarization(max_length=500),
    processors.SaveToFile("output", format="json")
])

# Process audio
result = pipeline.process("noisy_lecture.mp3")
```

### 6. Long Recording Sessions

```python
from green_needle import AudioRecorder, Transcriber
import time

# Set up recorder
recorder = AudioRecorder(sample_rate=16000)

# Start recording
output_path = recorder.record(
    "session.wav",
    duration=7200,  # 2 hours
    auto_stop_silence=True,
    silence_duration=30.0  # Stop after 30s of silence
)

# Monitor recording
while recorder.is_recording:
    time.sleep(10)
    print("Still recording...")

# Transcribe when done
transcriber = Transcriber(model="base")
result = transcriber.transcribe(output_path)

# Save transcript
result.save("session_transcript.txt")
```

### 7. Real-time Processing

```python
from green_needle import AudioRecorder, Transcriber
import threading
import queue

# Queue for audio chunks
audio_queue = queue.Queue()

def record_chunks():
    """Record audio in chunks."""
    recorder = AudioRecorder()
    # Implementation for chunk recording
    pass

def transcribe_chunks():
    """Transcribe audio chunks as they arrive."""
    transcriber = Transcriber(model="tiny")  # Fast model
    
    while True:
        chunk = audio_queue.get()
        if chunk is None:
            break
        
        result = transcriber.transcribe(chunk)
        print(f"Transcribed: {result.text}")

# Start threads
record_thread = threading.Thread(target=record_chunks)
transcribe_thread = threading.Thread(target=transcribe_chunks)

record_thread.start()
transcribe_thread.start()
```

## Advanced Configuration

### 1. Custom Config File

Create `my-config.yaml`:

```yaml
whisper:
  model: medium
  device: cuda
  
audio:
  sample_rate: 16000
  
output:
  format: json
  timestamps: true
  
processing:
  num_workers: 4
  chunk_duration: 1800.0
```

Use it:

```bash
green-needle --config my-config.yaml transcribe audio.mp3
```

### 2. Environment Variables

```bash
export GREEN_NEEDLE_MODEL=large
export GREEN_NEEDLE_DEVICE=cuda
green-needle transcribe audio.mp3
```

## Docker Usage

### 1. Basic Docker Run

```bash
docker run -v $(pwd):/app/input greenneedle/transcriber \
    transcribe /app/input/audio.mp3
```

### 2. GPU Support

```bash
docker run --gpus all -v $(pwd):/app/input greenneedle/transcriber:gpu \
    transcribe /app/input/audio.mp3 --model large
```

### 3. Docker Compose

```bash
# Process single file
docker-compose run green-needle

# Batch processing
docker-compose run green-needle-batch
```

## Tips and Tricks

### 1. Optimal Settings for Different Use Cases

**Podcasts/Interviews:**
```bash
green-needle transcribe podcast.mp3 --model small --initial-prompt "Interview transcript"
```

**Lectures/Presentations:**
```bash
green-needle transcribe lecture.mp4 --model medium --word-timestamps
```

**Quick Drafts:**
```bash
green-needle transcribe notes.mp3 --model tiny --format txt
```

### 2. Handling Large Files

For files over 1 hour, consider:
- Using batch processing with auto-split
- Increasing system memory
- Using GPU acceleration
- Processing overnight

### 3. Multi-language Content

```python
# Detect language first
languages = transcriber.detect_language("multilingual.mp3")

# Transcribe with detected language
result = transcriber.transcribe(
    "multilingual.mp3",
    language=max(languages, key=languages.get)
)
```