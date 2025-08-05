"""Transcription result handling and formatting."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from .utils import format_timestamp, ensure_dir


class TranscriptionResult:
    """Container for transcription results with multiple output formats."""
    
    def __init__(
        self,
        text: str,
        segments: List[Dict[str, Any]],
        language: str,
        duration: float,
        audio_path: str,
        model: str,
        task: str = "transcribe"
    ):
        """
        Initialize transcription result.
        
        Args:
            text: Full transcribed text
            segments: List of segment dictionaries from Whisper
            language: Detected or specified language code
            duration: Transcription duration in seconds
            audio_path: Path to source audio file
            model: Whisper model used
            task: Task performed (transcribe or translate)
        """
        self.text = text
        self.segments = segments
        self.language = language
        self.duration = duration
        self.audio_path = audio_path
        self.model = model
        self.task = task
        self.created_at = datetime.now()
    
    def save(self, output_path: Union[str, Path], format: str = "txt") -> Path:
        """
        Save transcription in specified format.
        
        Args:
            output_path: Output file path
            format: Output format (txt, json, srt, vtt, tsv, all)
            
        Returns:
            Path to saved file(s)
        """
        output_path = Path(output_path)
        ensure_dir(output_path.parent)
        
        if format == "all":
            # Save in all formats
            base_path = output_path.with_suffix("")
            saved_paths = []
            for fmt in ["txt", "json", "srt", "vtt", "tsv"]:
                path = base_path.with_suffix(f".{fmt}")
                self._save_single_format(path, fmt)
                saved_paths.append(path)
            return saved_paths[0]  # Return the first one
        else:
            # Ensure correct extension
            if not output_path.suffix == f".{format}":
                output_path = output_path.with_suffix(f".{format}")
            
            self._save_single_format(output_path, format)
            return output_path
    
    def _save_single_format(self, path: Path, format: str):
        """Save in a single format."""
        if format == "txt":
            self._save_txt(path)
        elif format == "json":
            self._save_json(path)
        elif format == "srt":
            self._save_srt(path)
        elif format == "vtt":
            self._save_vtt(path)
        elif format == "tsv":
            self._save_tsv(path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _save_txt(self, path: Path):
        """Save as plain text."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text)
    
    def _save_json(self, path: Path):
        """Save as JSON with metadata."""
        data = {
            "text": self.text,
            "segments": self.segments,
            "language": self.language,
            "duration": self.duration,
            "audio_path": self.audio_path,
            "model": self.model,
            "task": self.task,
            "created_at": self.created_at.isoformat(),
            "word_count": len(self.text.split()),
            "char_count": len(self.text)
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_srt(self, path: Path):
        """Save as SRT subtitle file."""
        with open(path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(self.segments, 1):
                start = format_timestamp(segment["start"], format="srt")
                end = format_timestamp(segment["end"], format="srt")
                text = segment["text"].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n")
                f.write("\n")
    
    def _save_vtt(self, path: Path):
        """Save as WebVTT subtitle file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            
            for segment in self.segments:
                start = format_timestamp(segment["start"], format="vtt")
                end = format_timestamp(segment["end"], format="vtt")
                text = segment["text"].strip()
                
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n")
                f.write("\n")
    
    def _save_tsv(self, path: Path):
        """Save as TSV (tab-separated values) file."""
        with open(path, "w", encoding="utf-8") as f:
            # Write header
            f.write("start\tend\ttext\n")
            
            # Write segments
            for segment in self.segments:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"].strip().replace("\t", " ")
                f.write(f"{start:.3f}\t{end:.3f}\t{text}\n")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the transcription."""
        return {
            "audio_path": self.audio_path,
            "language": self.language,
            "model": self.model,
            "task": self.task,
            "duration": self.duration,
            "created_at": self.created_at.isoformat(),
            "word_count": len(self.text.split()),
            "char_count": len(self.text),
            "segment_count": len(self.segments),
            "average_segment_duration": (
                sum(s["end"] - s["start"] for s in self.segments) / len(self.segments)
                if self.segments else 0
            )
        }
    
    def get_summary(self) -> str:
        """Get a summary of the transcription."""
        word_count = len(self.text.split())
        duration_str = str(timedelta(seconds=int(self.duration)))
        
        return (
            f"Transcription Summary:\n"
            f"- Audio: {Path(self.audio_path).name}\n"
            f"- Language: {self.language}\n"
            f"- Words: {word_count:,}\n"
            f"- Segments: {len(self.segments)}\n"
            f"- Processing time: {duration_str}\n"
            f"- Model: {self.model}"
        )
    
    def __str__(self):
        """String representation."""
        return self.text
    
    def __repr__(self):
        """Debug representation."""
        return (
            f"TranscriptionResult("
            f"text_length={len(self.text)}, "
            f"segments={len(self.segments)}, "
            f"language='{self.language}')"
        )