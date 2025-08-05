"""Custom exceptions for Green Needle."""


class GreenNeedleError(Exception):
    """Base exception for Green Needle."""
    pass


class TranscriptionError(GreenNeedleError):
    """Error during transcription process."""
    pass


class RecordingError(GreenNeedleError):
    """Error during audio recording."""
    pass


class ModelLoadError(GreenNeedleError):
    """Error loading Whisper model."""
    pass


class ConfigError(GreenNeedleError):
    """Error in configuration."""
    pass


class AudioProcessingError(GreenNeedleError):
    """Error processing audio file."""
    pass


class BatchProcessingError(GreenNeedleError):
    """Error during batch processing."""
    pass