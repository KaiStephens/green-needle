"""Audio processing pipeline for Green Needle."""

import logging
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
from abc import ABC, abstractmethod

import numpy as np

from .utils import ensure_dir
from .exceptions import AudioProcessingError

logger = logging.getLogger(__name__)


class Processor(ABC):
    """Base class for pipeline processors."""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data and return result."""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}()"


class Pipeline:
    """Audio processing pipeline with multiple stages."""
    
    def __init__(self, processors: List[Processor]):
        """
        Initialize pipeline with list of processors.
        
        Args:
            processors: List of Processor instances
        """
        self.processors = processors
    
    def process(self, input_data: Any) -> Any:
        """
        Process data through all pipeline stages.
        
        Args:
            input_data: Initial input data
            
        Returns:
            Final processed result
        """
        result = input_data
        
        for processor in self.processors:
            logger.debug(f"Running processor: {processor}")
            try:
                result = processor.process(result)
            except Exception as e:
                raise AudioProcessingError(
                    f"Pipeline failed at {processor}: {str(e)}"
                )
        
        return result
    
    def add_processor(self, processor: Processor):
        """Add a processor to the pipeline."""
        self.processors.append(processor)
    
    def remove_processor(self, processor_type: type):
        """Remove processors of a specific type."""
        self.processors = [p for p in self.processors 
                          if not isinstance(p, processor_type)]
    
    def __repr__(self):
        stages = " -> ".join(repr(p) for p in self.processors)
        return f"Pipeline({stages})"


# Standard processors module
class processors:
    """Collection of standard audio processors."""
    
    class AudioLoader(Processor):
        """Load audio from file."""
        
        def __init__(self, sample_rate: int = 16000):
            self.sample_rate = sample_rate
        
        def process(self, file_path: Union[str, Path]) -> Dict[str, Any]:
            import soundfile as sf
            
            audio, sr = sf.read(str(file_path))
            
            # Resample if necessary
            if sr != self.sample_rate:
                import librosa
                audio = librosa.resample(
                    audio, orig_sr=sr, target_sr=self.sample_rate
                )
            
            return {
                'audio': audio,
                'sample_rate': self.sample_rate,
                'file_path': str(file_path)
            }
    
    class NoiseReduction(Processor):
        """Reduce noise in audio."""
        
        def __init__(self, stationary: bool = True, prop_decrease: float = 1.0):
            self.stationary = stationary
            self.prop_decrease = prop_decrease
        
        def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                import noisereduce as nr
                
                audio = data['audio']
                sr = data['sample_rate']
                
                # Apply noise reduction
                reduced_audio = nr.reduce_noise(
                    y=audio,
                    sr=sr,
                    stationary=self.stationary,
                    prop_decrease=self.prop_decrease
                )
                
                data['audio'] = reduced_audio
                return data
                
            except ImportError:
                logger.warning("noisereduce not installed, skipping noise reduction")
                return data
    
    class VoiceActivityDetection(Processor):
        """Detect and extract voice segments."""
        
        def __init__(self, aggressiveness: int = 1):
            self.aggressiveness = aggressiveness
        
        def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
            import webrtcvad
            
            vad = webrtcvad.Vad(self.aggressiveness)
            audio = data['audio']
            sample_rate = data['sample_rate']
            
            # Convert to 16-bit PCM
            if audio.dtype != np.int16:
                audio = (audio * 32767).astype(np.int16)
            
            # Process in 30ms frames
            frame_duration = 30  # ms
            frame_length = int(sample_rate * frame_duration / 1000)
            
            voiced_frames = []
            for i in range(0, len(audio) - frame_length, frame_length):
                frame = audio[i:i + frame_length].tobytes()
                if vad.is_speech(frame, sample_rate):
                    voiced_frames.extend(audio[i:i + frame_length])
            
            data['audio'] = np.array(voiced_frames, dtype=audio.dtype)
            data['vad_applied'] = True
            
            return data
    
    class WhisperTranscription(Processor):
        """Transcribe audio using Whisper."""
        
        def __init__(self, model: str = "base", **kwargs):
            from .transcriber import Transcriber
            self.transcriber = Transcriber(model=model)
            self.kwargs = kwargs
        
        def process(self, data: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
            # Handle different input types
            if isinstance(data, (str, Path)):
                file_path = data
            elif isinstance(data, dict) and 'file_path' in data:
                file_path = data['file_path']
            else:
                # Save audio to temporary file
                import tempfile
                import soundfile as sf
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    sf.write(tmp.name, data['audio'], data['sample_rate'])
                    file_path = tmp.name
            
            # Transcribe
            result = self.transcriber.transcribe(file_path, **self.kwargs)
            
            # Return enriched data
            if isinstance(data, dict):
                data['transcription'] = result
                data['text'] = result.text
                data['segments'] = result.segments
                return data
            else:
                return {
                    'file_path': str(file_path),
                    'transcription': result,
                    'text': result.text,
                    'segments': result.segments
                }
    
    class TextPostProcessing(Processor):
        """Post-process transcribed text."""
        
        def __init__(
            self,
            fix_punctuation: bool = True,
            remove_filler_words: bool = False,
            capitalize_sentences: bool = True
        ):
            self.fix_punctuation = fix_punctuation
            self.remove_filler_words = remove_filler_words
            self.capitalize_sentences = capitalize_sentences
        
        def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
            text = data.get('text', '')
            
            if self.remove_filler_words:
                filler_words = ['um', 'uh', 'like', 'you know', 'er', 'ah']
                for filler in filler_words:
                    text = text.replace(f' {filler} ', ' ')
                    text = text.replace(f' {filler}, ', ' ')
                    text = text.replace(f' {filler}. ', '. ')
            
            if self.fix_punctuation:
                # Basic punctuation fixes
                text = text.replace(' ,', ',')
                text = text.replace(' .', '.')
                text = text.replace(' ?', '?')
                text = text.replace(' !', '!')
                text = text.replace(' :', ':')
                text = text.replace(' ;', ';')
            
            if self.capitalize_sentences:
                import re
                # Capitalize first letter after sentence endings
                text = re.sub(r'([.!?]\s*)([a-z])', 
                             lambda m: m.group(1) + m.group(2).upper(), text)
                # Capitalize first letter
                if text and text[0].islower():
                    text = text[0].upper() + text[1:]
            
            data['text'] = text
            return data
    
    class Summarization(Processor):
        """Summarize long transcripts."""
        
        def __init__(self, max_length: int = 500, min_length: int = 100):
            self.max_length = max_length
            self.min_length = min_length
        
        def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
            text = data.get('text', '')
            
            # Simple extractive summarization
            # In production, you might use transformers or other NLP libraries
            sentences = text.split('. ')
            
            if len(sentences) <= 5:
                data['summary'] = text
            else:
                # Take first and last sentences plus some from middle
                summary_sentences = [
                    sentences[0],
                    sentences[len(sentences)//3],
                    sentences[2*len(sentences)//3],
                    sentences[-1]
                ]
                data['summary'] = '. '.join(summary_sentences) + '.'
            
            return data
    
    class SaveToFile(Processor):
        """Save results to file."""
        
        def __init__(
            self,
            output_dir: Union[str, Path],
            format: str = "txt",
            save_audio: bool = False
        ):
            self.output_dir = Path(output_dir)
            self.format = format
            self.save_audio = save_audio
            ensure_dir(self.output_dir)
        
        def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
            # Generate output filename
            if 'file_path' in data:
                base_name = Path(data['file_path']).stem
            else:
                import time
                base_name = f"output_{int(time.time())}"
            
            # Save transcription
            if 'transcription' in data:
                result = data['transcription']
                output_path = self.output_dir / f"{base_name}.{self.format}"
                result.save(output_path, format=self.format)
                data['output_path'] = str(output_path)
            
            # Save processed audio if requested
            if self.save_audio and 'audio' in data:
                import soundfile as sf
                audio_path = self.output_dir / f"{base_name}_processed.wav"
                sf.write(str(audio_path), data['audio'], data['sample_rate'])
                data['processed_audio_path'] = str(audio_path)
            
            return data


# Pre-built pipelines
def create_standard_pipeline(model: str = "base", output_dir: str = "output") -> Pipeline:
    """Create standard transcription pipeline."""
    return Pipeline([
        processors.AudioLoader(),
        processors.NoiseReduction(),
        processors.WhisperTranscription(model=model),
        processors.TextPostProcessing(),
        processors.SaveToFile(output_dir)
    ])


def create_voice_only_pipeline(model: str = "base", output_dir: str = "output") -> Pipeline:
    """Create pipeline that extracts voice segments before transcription."""
    return Pipeline([
        processors.AudioLoader(),
        processors.VoiceActivityDetection(aggressiveness=2),
        processors.NoiseReduction(),
        processors.WhisperTranscription(model=model),
        processors.TextPostProcessing(),
        processors.SaveToFile(output_dir)
    ])


def create_summarization_pipeline(model: str = "base", output_dir: str = "output") -> Pipeline:
    """Create pipeline with summarization."""
    return Pipeline([
        processors.AudioLoader(),
        processors.WhisperTranscription(model=model),
        processors.TextPostProcessing(),
        processors.Summarization(),
        processors.SaveToFile(output_dir)
    ])