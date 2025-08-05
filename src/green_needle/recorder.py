"""Audio recording functionality for long-form content."""

import os
import time
import wave
import threading
import queue
import logging
from pathlib import Path
from typing import Optional, Callable, Union
from datetime import datetime, timedelta

import sounddevice as sd
import numpy as np
import soundfile as sf

from .utils import ensure_dir, format_size
from .exceptions import RecordingError

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Record audio from microphone with support for long recordings."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: Optional[int] = None,
        dtype: str = "float32"
    ):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Sample rate in Hz (16000 recommended for Whisper)
            channels: Number of channels (1 for mono, 2 for stereo)
            device: Audio device index (None for default)
            dtype: Audio data type
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.dtype = dtype
        
        # Recording state
        self._recording = False
        self._pause = False
        self._audio_queue = queue.Queue()
        self._recording_thread = None
        
        # Validate audio setup
        self._validate_audio_setup()
    
    def _validate_audio_setup(self):
        """Validate that audio recording is possible."""
        try:
            # Test recording for a brief moment
            test_recording = sd.rec(
                int(0.1 * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                dtype=self.dtype
            )
            sd.wait()
            logger.info("Audio setup validated successfully")
        except Exception as e:
            raise RecordingError(f"Audio setup validation failed: {str(e)}")
    
    def record(
        self,
        output_path: Union[str, Path],
        duration: Optional[float] = None,
        callback: Optional[Callable[[float], None]] = None,
        auto_stop_silence: bool = False,
        silence_threshold: float = 0.01,
        silence_duration: float = 3.0
    ) -> Path:
        """
        Record audio to file.
        
        Args:
            output_path: Path to save the recording
            duration: Maximum duration in seconds (None for unlimited)
            callback: Progress callback function
            auto_stop_silence: Automatically stop on silence
            silence_threshold: RMS threshold for silence detection
            silence_duration: Duration of silence before auto-stop
            
        Returns:
            Path to the recorded audio file
        """
        output_path = Path(output_path)
        ensure_dir(output_path.parent)
        
        logger.info(f"Starting recording to: {output_path}")
        if duration:
            logger.info(f"Maximum duration: {duration} seconds")
        
        # Start recording in a separate thread
        self._recording = True
        self._recording_thread = threading.Thread(
            target=self._record_worker,
            args=(output_path, duration, callback, auto_stop_silence, 
                  silence_threshold, silence_duration)
        )
        self._recording_thread.start()
        
        return output_path
    
    def _record_worker(
        self,
        output_path: Path,
        duration: Optional[float],
        callback: Optional[Callable[[float], None]],
        auto_stop_silence: bool,
        silence_threshold: float,
        silence_duration: float
    ):
        """Worker thread for recording."""
        try:
            start_time = time.time()
            audio_data = []
            silence_start = None
            
            def audio_callback(indata, frames, time_info, status):
                """Callback for audio stream."""
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                if self._recording and not self._pause:
                    self._audio_queue.put(indata.copy())
            
            # Open audio stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                dtype=self.dtype,
                callback=audio_callback
            ):
                logger.info("Recording started")
                
                while self._recording:
                    try:
                        # Get audio chunk with timeout
                        chunk = self._audio_queue.get(timeout=0.1)
                        audio_data.append(chunk)
                        
                        # Calculate elapsed time
                        elapsed = time.time() - start_time
                        
                        # Progress callback
                        if callback:
                            progress = (elapsed / duration * 100) if duration else elapsed
                            callback(progress)
                        
                        # Check duration limit
                        if duration and elapsed >= duration:
                            logger.info("Duration limit reached")
                            break
                        
                        # Silence detection
                        if auto_stop_silence:
                            rms = np.sqrt(np.mean(chunk**2))
                            
                            if rms < silence_threshold:
                                if silence_start is None:
                                    silence_start = time.time()
                                elif time.time() - silence_start >= silence_duration:
                                    logger.info("Stopping due to silence")
                                    break
                            else:
                                silence_start = None
                    
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Recording error: {str(e)}")
                        break
            
            # Combine audio data
            if audio_data:
                audio_array = np.concatenate(audio_data, axis=0)
                
                # Save audio file
                sf.write(
                    str(output_path),
                    audio_array,
                    self.sample_rate,
                    subtype='PCM_16'
                )
                
                duration_str = str(timedelta(seconds=int(time.time() - start_time)))
                size_str = format_size(output_path.stat().st_size)
                logger.info(f"Recording saved: {output_path} "
                           f"(duration: {duration_str}, size: {size_str})")
            else:
                raise RecordingError("No audio data recorded")
                
        except Exception as e:
            logger.error(f"Recording failed: {str(e)}")
            raise RecordingError(f"Recording failed: {str(e)}")
        finally:
            self._recording = False
    
    def stop(self):
        """Stop recording."""
        logger.info("Stopping recording")
        self._recording = False
        
        if self._recording_thread:
            self._recording_thread.join(timeout=5.0)
    
    def pause(self):
        """Pause recording."""
        logger.info("Pausing recording")
        self._pause = True
    
    def resume(self):
        """Resume recording."""
        logger.info("Resuming recording")
        self._pause = False
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
    
    @property
    def is_paused(self) -> bool:
        """Check if recording is paused."""
        return self._pause
    
    @staticmethod
    def list_devices():
        """List available audio devices."""
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        
        return input_devices
    
    def record_interactive(
        self,
        output_dir: Union[str, Path] = "recordings",
        prefix: str = "recording",
        format: str = "wav"
    ) -> Path:
        """
        Interactive recording with keyboard controls.
        
        Args:
            output_dir: Directory to save recordings
            prefix: Filename prefix
            format: Audio format
            
        Returns:
            Path to recorded file
        """
        output_dir = Path(output_dir)
        ensure_dir(output_dir)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{format}"
        output_path = output_dir / filename
        
        print(f"Recording to: {output_path}")
        print("Press Enter to stop recording...")
        print("Press 'p' to pause/resume")
        
        # Start recording
        self.record(output_path)
        
        try:
            while self.is_recording:
                user_input = input().strip().lower()
                
                if user_input == "":
                    self.stop()
                    break
                elif user_input == "p":
                    if self.is_paused:
                        self.resume()
                        print("Resumed")
                    else:
                        self.pause()
                        print("Paused")
        except KeyboardInterrupt:
            self.stop()
        
        print(f"Recording saved: {output_path}")
        return output_path