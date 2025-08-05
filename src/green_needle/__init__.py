"""Green Needle - High-quality local audio transcription using OpenAI Whisper."""

from .transcriber import Transcriber
from .recorder import AudioRecorder
from .pipeline import Pipeline
from .batch_processor import BatchProcessor
from .version import __version__

__all__ = [
    "Transcriber",
    "AudioRecorder", 
    "Pipeline",
    "BatchProcessor",
    "__version__"
]