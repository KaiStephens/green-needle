"""Tests for the Transcriber class."""

import pytest
from pathlib import Path
import tempfile
import numpy as np
import soundfile as sf

from green_needle.transcriber import Transcriber
from green_needle.exceptions import TranscriptionError, ModelLoadError


@pytest.fixture
def sample_audio():
    """Create a sample audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        # Generate 5 seconds of silence
        sample_rate = 16000
        duration = 5
        audio = np.zeros((sample_rate * duration,))
        
        # Add some noise to avoid complete silence
        audio += np.random.normal(0, 0.01, audio.shape)
        
        sf.write(tmp.name, audio, sample_rate)
        yield tmp.name
        Path(tmp.name).unlink()


@pytest.fixture
def transcriber():
    """Create a transcriber instance with tiny model for fast tests."""
    return Transcriber(model="tiny", device="cpu")


class TestTranscriber:
    """Test cases for Transcriber class."""
    
    def test_init(self):
        """Test transcriber initialization."""
        t = Transcriber(model="tiny", device="cpu")
        assert t.model_name == "tiny"
        assert t.device == "cpu"
    
    def test_device_detection(self):
        """Test automatic device detection."""
        t = Transcriber(model="tiny")
        assert t.device in ["cpu", "cuda", "mps"]
    
    def test_model_loading(self, transcriber):
        """Test model loading."""
        model = transcriber.model
        assert model is not None
    
    def test_transcribe_file(self, transcriber, sample_audio):
        """Test basic transcription."""
        result = transcriber.transcribe(sample_audio)
        
        assert result is not None
        assert isinstance(result.text, str)
        assert result.language is not None
        assert result.audio_path == sample_audio
    
    def test_transcribe_nonexistent_file(self, transcriber):
        """Test transcription with non-existent file."""
        with pytest.raises(FileNotFoundError):
            transcriber.transcribe("nonexistent.mp3")
    
    def test_language_detection(self, transcriber, sample_audio):
        """Test language detection."""
        languages = transcriber.detect_language(sample_audio)
        
        assert isinstance(languages, dict)
        assert len(languages) > 0
        assert all(isinstance(prob, float) for prob in languages.values())
        assert sum(languages.values()) == pytest.approx(1.0, rel=0.01)
    
    def test_batch_transcribe(self, transcriber, sample_audio):
        """Test batch transcription."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = transcriber.batch_transcribe(
                [sample_audio],
                output_dir=tmpdir,
                format="txt"
            )
            
            assert len(results) == 1
            assert results[0] is not None
            
            # Check output file was created
            output_file = Path(tmpdir) / f"{Path(sample_audio).stem}.txt"
            assert output_file.exists()
    
    def test_invalid_model(self):
        """Test initialization with invalid model."""
        with pytest.raises(ModelLoadError):
            t = Transcriber(model="invalid_model")
            _ = t.model  # Force model loading
    
    @pytest.mark.parametrize("model", ["tiny", "base"])
    def test_different_models(self, model, sample_audio):
        """Test transcription with different models."""
        t = Transcriber(model=model, device="cpu")
        result = t.transcribe(sample_audio)
        assert result is not None