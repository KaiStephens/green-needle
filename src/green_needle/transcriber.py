"""Core transcription functionality using OpenAI Whisper."""

import os
import logging
import warnings
from typing import Dict, List, Optional, Union, Callable, Any
from pathlib import Path
import json
from datetime import datetime

import whisper
import torch
import numpy as np
from tqdm import tqdm

from .utils import format_timestamp, ensure_dir
from .result import TranscriptionResult
from .exceptions import TranscriptionError, ModelLoadError

# Suppress warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

logger = logging.getLogger(__name__)


class Transcriber:
    """Main transcription engine using OpenAI Whisper models."""
    
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    SUPPORTED_FORMATS = ["txt", "json", "srt", "vtt", "tsv", "all"]
    
    def __init__(
        self,
        model: str = "base",
        device: Optional[str] = None,
        download_root: Optional[str] = None,
        in_memory: bool = True
    ):
        """
        Initialize the transcriber with specified model.
        
        Args:
            model: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda, cpu, or None for auto-detect)
            download_root: Directory to download models to
            in_memory: Keep model in memory between transcriptions
        """
        self.model_name = model
        self.device = self._get_device(device)
        self.download_root = download_root
        self.in_memory = in_memory
        self._model = None
        
        logger.info(f"Initializing Transcriber with model '{model}' on device '{self.device}'")
        
        if self.in_memory:
            self._load_model()
    
    def _get_device(self, device: Optional[str]) -> str:
        """Determine the best device to use."""
        if device:
            return device
            
        if torch.cuda.is_available():
            logger.info("CUDA available, using GPU")
            return "cuda"
        elif torch.backends.mps.is_available():
            logger.info("MPS available, using Apple Silicon GPU")
            return "mps"
        else:
            logger.info("Using CPU")
            return "cpu"
    
    def _load_model(self) -> whisper.Whisper:
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model '{self.model_name}'...")
            model = whisper.load_model(
                self.model_name,
                device=self.device,
                download_root=self.download_root
            )
            logger.info("Model loaded successfully")
            return model
        except Exception as e:
            raise ModelLoadError(f"Failed to load model '{self.model_name}': {str(e)}")
    
    @property
    def model(self) -> whisper.Whisper:
        """Get the loaded model, loading it if necessary."""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe",
        temperature: Union[float, List[float]] = 0.0,
        compression_ratio_threshold: float = 2.4,
        logprob_threshold: float = -1.0,
        no_speech_threshold: float = 0.6,
        condition_on_previous_text: bool = True,
        initial_prompt: Optional[str] = None,
        word_timestamps: bool = False,
        prepend_punctuations: str = r'"\'¿([{-',
        append_punctuations: str = r'"\'.。,，!！?？:：")]}、',
        verbose: Optional[bool] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            task: Task to perform ('transcribe' or 'translate')
            temperature: Temperature for sampling
            compression_ratio_threshold: Threshold for compression ratio
            logprob_threshold: Threshold for log probability
            no_speech_threshold: Threshold for no speech detection
            condition_on_previous_text: Whether to condition on previous text
            initial_prompt: Initial prompt to help with transcription
            word_timestamps: Whether to include word-level timestamps
            prepend_punctuations: Punctuations to prepend
            append_punctuations: Punctuations to append
            verbose: Whether to display progress
            progress_callback: Callback function for progress updates
            **kwargs: Additional arguments passed to whisper.transcribe
            
        Returns:
            TranscriptionResult object containing the transcription
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Starting transcription of: {audio_path}")
        start_time = datetime.now()
        
        try:
            # Set up progress tracking
            if verbose is None:
                verbose = progress_callback is not None
            
            # Prepare transcription options
            options = {
                "language": language,
                "task": task,
                "temperature": temperature,
                "compression_ratio_threshold": compression_ratio_threshold,
                "logprob_threshold": logprob_threshold,
                "no_speech_threshold": no_speech_threshold,
                "condition_on_previous_text": condition_on_previous_text,
                "initial_prompt": initial_prompt,
                "word_timestamps": word_timestamps,
                "prepend_punctuations": prepend_punctuations,
                "append_punctuations": append_punctuations,
                "verbose": verbose,
                **kwargs
            }
            
            # Perform transcription
            if progress_callback:
                # Wrap the transcribe call to track progress
                result = self._transcribe_with_progress(
                    str(audio_path),
                    options,
                    progress_callback
                )
            else:
                result = self.model.transcribe(str(audio_path), **options)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Create result object
            transcription_result = TranscriptionResult(
                text=result["text"],
                segments=result.get("segments", []),
                language=result.get("language", language),
                duration=duration,
                audio_path=str(audio_path),
                model=self.model_name,
                task=task
            )
            
            logger.info(f"Transcription completed in {duration:.2f} seconds")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise TranscriptionError(f"Failed to transcribe {audio_path}: {str(e)}")
    
    def _transcribe_with_progress(
        self,
        audio_path: str,
        options: Dict[str, Any],
        progress_callback: Callable[[float], None]
    ) -> Dict[str, Any]:
        """Transcribe with progress tracking."""
        # This is a simplified version - in production you might want to
        # hook into Whisper's internal progress tracking
        progress_callback(0.0)
        result = self.model.transcribe(audio_path, **options)
        progress_callback(100.0)
        return result
    
    def detect_language(self, audio_path: Union[str, Path]) -> Dict[str, float]:
        """
        Detect the language of an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary of language codes and their probabilities
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Detecting language for: {audio_path}")
        
        # Load audio
        audio = whisper.load_audio(str(audio_path))
        audio = whisper.pad_or_trim(audio)
        
        # Make log-Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio).to(self.device)
        
        # Detect language
        _, probs = self.model.detect_language(mel)
        
        # Sort by probability
        sorted_probs = dict(sorted(probs.items(), key=lambda x: x[1], reverse=True))
        
        logger.info(f"Detected language: {list(sorted_probs.keys())[0]} "
                   f"(confidence: {list(sorted_probs.values())[0]:.2%})")
        
        return sorted_probs
    
    def batch_transcribe(
        self,
        audio_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None,
        format: str = "txt",
        num_workers: int = 1,
        **transcribe_kwargs
    ) -> List[TranscriptionResult]:
        """
        Transcribe multiple audio files.
        
        Args:
            audio_paths: List of audio file paths
            output_dir: Directory to save transcriptions
            format: Output format
            num_workers: Number of parallel workers (currently single-threaded)
            **transcribe_kwargs: Arguments passed to transcribe()
            
        Returns:
            List of TranscriptionResult objects
        """
        results = []
        
        for audio_path in tqdm(audio_paths, desc="Transcribing files"):
            try:
                result = self.transcribe(audio_path, **transcribe_kwargs)
                results.append(result)
                
                # Save if output directory specified
                if output_dir:
                    output_path = Path(output_dir) / f"{Path(audio_path).stem}.{format}"
                    result.save(output_path, format=format)
                    
            except Exception as e:
                logger.error(f"Failed to transcribe {audio_path}: {str(e)}")
                continue
        
        return results
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, '_model') and self._model is not None:
            del self._model
            torch.cuda.empty_cache() if self.device == "cuda" else None