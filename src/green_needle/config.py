"""Configuration management for Green Needle."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml
from dataclasses import dataclass, field, asdict

from .exceptions import ConfigError


@dataclass
class WhisperConfig:
    """Whisper model configuration."""
    model: str = "base"
    language: Optional[str] = None
    device: str = "auto"
    download_root: Optional[str] = None
    

@dataclass
class AudioConfig:
    """Audio recording configuration."""
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "float32"
    device: Optional[int] = None
    

@dataclass
class OutputConfig:
    """Output configuration."""
    format: str = "txt"
    timestamps: bool = False
    save_segments: bool = True
    output_dir: str = "output"
    

@dataclass
class ProcessingConfig:
    """Processing configuration."""
    batch_size: int = 10
    num_workers: int = 1
    chunk_duration: float = 3600.0
    auto_split: bool = True
    

@dataclass
class Config:
    """Main configuration class."""
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Config":
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Create nested configs
            config = cls()
            
            if 'whisper' in data:
                config.whisper = WhisperConfig(**data['whisper'])
            if 'audio' in data:
                config.audio = AudioConfig(**data['audio'])
            if 'output' in data:
                config.output = OutputConfig(**data['output'])
            if 'processing' in data:
                config.processing = ProcessingConfig(**data['processing'])
            
            return config
            
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def save(self, path: Union[str, Path]):
        """Save configuration to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'whisper': asdict(self.whisper),
            'audio': asdict(self.audio),
            'output': asdict(self.output),
            'processing': asdict(self.processing)
        }
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string."""
        data = {
            'whisper': asdict(self.whisper),
            'audio': asdict(self.audio),
            'output': asdict(self.output),
            'processing': asdict(self.processing)
        }
        
        return yaml.dump(data, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        parts = key.split('.')
        value = self
        
        try:
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return default
            return value
        except:
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key."""
        parts = key.split('.')
        
        if len(parts) < 2:
            raise ConfigError(f"Invalid configuration key: {key}")
        
        # Navigate to parent
        parent = self
        for part in parts[:-2]:
            parent = getattr(parent, part)
        
        # Set value
        section = getattr(parent, parts[-2])
        setattr(section, parts[-1], value)
    
    @classmethod
    def default_config_path(cls) -> Path:
        """Get default configuration file path."""
        # Try multiple locations
        locations = [
            Path.cwd() / "green-needle.yaml",
            Path.home() / ".config" / "green-needle" / "config.yaml",
            Path.home() / ".green-needle.yaml"
        ]
        
        for location in locations:
            if location.exists():
                return location
        
        # Return default location for new config
        return locations[1]  # ~/.config/green-needle/config.yaml
    
    def merge(self, other: "Config"):
        """Merge another configuration into this one."""
        for section in ['whisper', 'audio', 'output', 'processing']:
            other_section = getattr(other, section)
            self_section = getattr(self, section)
            
            for key, value in asdict(other_section).items():
                if value is not None:
                    setattr(self_section, key, value)


# Default configuration template
DEFAULT_CONFIG_TEMPLATE = """# Green Needle Configuration

whisper:
  model: base              # Model size: tiny, base, small, medium, large
  language: null          # Language code (null for auto-detect)
  device: auto           # Device: auto, cuda, cpu, mps
  download_root: null    # Custom model download directory

audio:
  sample_rate: 16000     # Sample rate in Hz
  channels: 1            # Number of channels (1=mono, 2=stereo)
  dtype: float32         # Audio data type
  device: null          # Audio device index (null for default)

output:
  format: txt            # Default output format
  timestamps: false      # Include timestamps in output
  save_segments: true    # Save individual segments
  output_dir: output     # Default output directory

processing:
  batch_size: 10         # Files to process in parallel
  num_workers: 1         # Number of worker processes
  chunk_duration: 3600.0 # Max chunk duration in seconds (1 hour)
  auto_split: true       # Automatically split long files
"""


def create_default_config(path: Optional[Union[str, Path]] = None):
    """Create default configuration file."""
    if path is None:
        path = Config.default_config_path()
    else:
        path = Path(path)
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(DEFAULT_CONFIG_TEMPLATE)
    
    return path