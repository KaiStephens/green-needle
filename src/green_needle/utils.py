"""Utility functions for Green Needle."""

import os
import logging
from pathlib import Path
from typing import Union, Optional
from datetime import timedelta
import subprocess
import platform

logger = logging.getLogger(__name__)


def format_timestamp(seconds: float, format: str = "srt") -> str:
    """
    Format timestamp for subtitle files.
    
    Args:
        seconds: Time in seconds
        format: Format type ('srt' or 'vtt')
        
    Returns:
        Formatted timestamp string
    """
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    milliseconds = td.microseconds // 1000
    
    if format == "srt":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    elif format == "vtt":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def ensure_dir(path: Union[str, Path]):
    """Ensure directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)


def get_audio_duration(file_path: Union[str, Path]) -> float:
    """
    Get duration of audio file in seconds.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        import soundfile as sf
        info = sf.info(str(file_path))
        return info.duration
    except Exception:
        # Fallback to ffprobe if available
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 
                 'format=duration', '-of', 
                 'default=noprint_wrappers=1:nokey=1', str(file_path)],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0


def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_system_info() -> dict:
    """Get system information for debugging."""
    import psutil
    import torch
    
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': format_size(psutil.virtual_memory().total),
        'memory_available': format_size(psutil.virtual_memory().available),
    }
    
    # Check GPU availability
    if torch.cuda.is_available():
        info['gpu'] = torch.cuda.get_device_name(0)
        info['gpu_memory'] = format_size(
            torch.cuda.get_device_properties(0).total_memory
        )
    elif torch.backends.mps.is_available():
        info['gpu'] = 'Apple Silicon GPU'
    else:
        info['gpu'] = 'None'
    
    # Check ffmpeg
    info['ffmpeg_available'] = check_ffmpeg()
    
    return info


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Set up logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def split_audio_file(
    file_path: Union[str, Path],
    chunk_duration: float = 3600.0,
    output_dir: Optional[Union[str, Path]] = None
) -> list:
    """
    Split large audio file into chunks.
    
    Args:
        file_path: Path to audio file
        chunk_duration: Duration of each chunk in seconds
        output_dir: Output directory for chunks
        
    Returns:
        List of chunk file paths
    """
    file_path = Path(file_path)
    
    if output_dir is None:
        output_dir = file_path.parent / f"{file_path.stem}_chunks"
    else:
        output_dir = Path(output_dir)
    
    ensure_dir(output_dir)
    
    # Get total duration
    total_duration = get_audio_duration(file_path)
    
    if total_duration <= chunk_duration:
        return [file_path]
    
    chunks = []
    num_chunks = int(total_duration / chunk_duration) + 1
    
    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_path = output_dir / f"{file_path.stem}_chunk_{i+1:03d}{file_path.suffix}"
        
        # Use ffmpeg to extract chunk
        cmd = [
            'ffmpeg', '-i', str(file_path),
            '-ss', str(start_time),
            '-t', str(chunk_duration),
            '-c', 'copy',
            '-y', str(chunk_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            chunks.append(chunk_path)
            logger.info(f"Created chunk: {chunk_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create chunk: {e}")
    
    return chunks