"""Batch processing functionality for multiple audio files."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from tqdm import tqdm

from .transcriber import Transcriber
from .utils import format_size, get_audio_duration
from .exceptions import BatchProcessingError

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple audio files efficiently."""
    
    def __init__(
        self,
        model: str = "base",
        device: Optional[str] = None,
        output_format: str = "txt",
        num_workers: int = 1,
        chunk_size: Optional[float] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            model: Whisper model to use
            device: Device for processing
            output_format: Output format for transcriptions
            num_workers: Number of parallel workers
            chunk_size: Maximum chunk size in seconds
        """
        self.model = model
        self.device = device
        self.output_format = output_format
        self.num_workers = num_workers
        self.chunk_size = chunk_size
        
        # Keep transcriber instances for reuse
        self._transcribers = {}
    
    def process_files(
        self,
        input_files: List[Union[str, Path]],
        output_dir: Union[str, Path],
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        skip_existing: bool = True,
        **transcribe_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process multiple audio files.
        
        Args:
            input_files: List of audio file paths
            output_dir: Output directory for transcriptions
            language: Language code for transcription
            progress_callback: Callback for progress updates
            skip_existing: Skip files that already have transcriptions
            **transcribe_kwargs: Additional arguments for transcription
            
        Returns:
            List of result dictionaries
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter files
        files_to_process = []
        for file_path in input_files:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            # Check if already processed
            output_path = output_dir / f"{file_path.stem}.{self.output_format}"
            if skip_existing and output_path.exists():
                logger.info(f"Skipping existing: {file_path.name}")
                continue
            
            files_to_process.append(file_path)
        
        if not files_to_process:
            logger.info("No files to process")
            return []
        
        logger.info(f"Processing {len(files_to_process)} files with {self.num_workers} workers")
        
        # Process files
        results = []
        completed = 0
        
        if self.num_workers == 1:
            # Sequential processing
            for file_path in files_to_process:
                result = self._process_single_file(
                    file_path,
                    output_dir,
                    language,
                    **transcribe_kwargs
                )
                results.append(result)
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(files_to_process))
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                # Submit tasks
                future_to_file = {
                    executor.submit(
                        self._process_single_file,
                        file_path,
                        output_dir,
                        language,
                        **transcribe_kwargs
                    ): file_path
                    for file_path in files_to_process
                }
                
                # Process results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to process {file_path}: {str(e)}")
                        results.append({
                            'file': str(file_path),
                            'success': False,
                            'error': str(e)
                        })
                    
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(files_to_process))
        
        return results
    
    def _process_single_file(
        self,
        file_path: Path,
        output_dir: Path,
        language: Optional[str] = None,
        **transcribe_kwargs
    ) -> Dict[str, Any]:
        """Process a single audio file."""
        start_time = datetime.now()
        
        try:
            # Get or create transcriber
            transcriber = self._get_transcriber()
            
            # Check file size and duration
            file_size = file_path.stat().st_size
            duration = get_audio_duration(file_path)
            
            logger.info(f"Processing: {file_path.name} "
                       f"(size: {format_size(file_size)}, "
                       f"duration: {duration:.1f}s)")
            
            # Transcribe
            result = transcriber.transcribe(
                file_path,
                language=language,
                **transcribe_kwargs
            )
            
            # Save result
            output_path = output_dir / f"{file_path.stem}.{self.output_format}"
            result.save(output_path, format=self.output_format)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'file': str(file_path),
                'success': True,
                'output': str(output_path),
                'duration': duration,
                'processing_time': processing_time,
                'real_time_factor': processing_time / duration if duration > 0 else 0,
                'language': result.language,
                'word_count': len(result.text.split())
            }
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return {
                'file': str(file_path),
                'success': False,
                'error': str(e)
            }
    
    def _get_transcriber(self) -> Transcriber:
        """Get or create a transcriber instance."""
        # Simple round-robin for now
        worker_id = len(self._transcribers)
        
        if worker_id not in self._transcribers:
            self._transcribers[worker_id] = Transcriber(
                model=self.model,
                device=self.device
            )
        
        return self._transcribers[worker_id]
    
    def process_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process all audio files in a directory.
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            pattern: File pattern to match
            recursive: Process subdirectories
            **kwargs: Additional arguments for process_files
            
        Returns:
            List of result dictionaries
        """
        input_dir = Path(input_dir)
        
        # Find audio files
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus', '.webm', '.mp4', '.avi', '.mkv'}
        
        if recursive:
            files = [f for f in input_dir.rglob(pattern) 
                    if f.is_file() and f.suffix.lower() in audio_extensions]
        else:
            files = [f for f in input_dir.glob(pattern) 
                    if f.is_file() and f.suffix.lower() in audio_extensions]
        
        if not files:
            logger.warning(f"No audio files found in {input_dir}")
            return []
        
        logger.info(f"Found {len(files)} audio files")
        
        return self.process_files(files, output_dir, **kwargs)
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a summary report of batch processing results."""
        total_files = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total_files - successful
        
        if successful > 0:
            success_results = [r for r in results if r['success']]
            total_duration = sum(r.get('duration', 0) for r in success_results)
            total_processing_time = sum(r.get('processing_time', 0) for r in success_results)
            total_words = sum(r.get('word_count', 0) for r in success_results)
            avg_rtf = total_processing_time / total_duration if total_duration > 0 else 0
            
            report = f"""
Batch Processing Report
======================
Total files: {total_files}
Successful: {successful}
Failed: {failed}

Processing Statistics:
- Total audio duration: {total_duration:.1f} seconds
- Total processing time: {total_processing_time:.1f} seconds
- Average real-time factor: {avg_rtf:.2f}x
- Total words transcribed: {total_words:,}

Language Distribution:
"""
            # Count languages
            languages = {}
            for r in success_results:
                lang = r.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
            
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                report += f"- {lang}: {count} files\n"
            
            if failed > 0:
                report += "\nFailed Files:\n"
                for r in results:
                    if not r['success']:
                        report += f"- {r['file']}: {r.get('error', 'Unknown error')}\n"
        else:
            report = "No files were successfully processed."
        
        return report