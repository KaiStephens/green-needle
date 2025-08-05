"""Command-line interface for Green Needle."""

import sys
import logging
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from .transcriber import Transcriber
from .recorder import AudioRecorder
from .batch_processor import BatchProcessor
from .config import Config
from .utils import format_size, setup_logging
from .version import __version__

console = Console()

# Set up logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="green-needle")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output")
@click.pass_context
def cli(ctx, config, verbose, quiet):
    """Green Needle - High-quality local audio transcription using OpenAI Whisper."""
    # Set up context
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        ctx.obj["config"] = Config.from_file(config)
    else:
        ctx.obj["config"] = Config()
    
    # Set logging level
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--model", "-m", default="base", 
              type=click.Choice(["tiny", "base", "small", "medium", "large"]),
              help="Whisper model size")
@click.option("--language", "-l", help="Language code (auto-detect if not specified)")
@click.option("--task", default="transcribe",
              type=click.Choice(["transcribe", "translate"]),
              help="Task to perform")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", default="txt",
              type=click.Choice(["txt", "json", "srt", "vtt", "tsv", "all"]),
              help="Output format")
@click.option("--device", help="Device to use (cuda, cpu, or auto)")
@click.option("--temperature", default=0.0, help="Temperature for sampling")
@click.option("--initial-prompt", help="Initial prompt to guide transcription")
@click.option("--word-timestamps", is_flag=True, help="Include word-level timestamps")
@click.pass_context
def transcribe(ctx, audio_file, model, language, task, output, format, device, 
               temperature, initial_prompt, word_timestamps):
    """Transcribe an audio file."""
    console.print(f"\n[bold blue]Transcribing:[/bold blue] {audio_file}")
    
    # Initialize transcriber
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Load model
        task_id = progress.add_task("Loading model...", total=None)
        transcriber = Transcriber(model=model, device=device)
        progress.remove_task(task_id)
        
        # Transcribe
        task_id = progress.add_task("Transcribing...", total=100)
        
        def update_progress(p):
            progress.update(task_id, completed=p)
        
        result = transcriber.transcribe(
            audio_file,
            language=language,
            task=task,
            temperature=temperature,
            initial_prompt=initial_prompt,
            word_timestamps=word_timestamps,
            progress_callback=update_progress
        )
        
        progress.remove_task(task_id)
    
    # Display summary
    console.print(f"\n[bold green]✓ Transcription complete![/bold green]")
    console.print(result.get_summary())
    
    # Save output
    if output:
        saved_path = result.save(output, format=format)
        console.print(f"\n[bold]Saved to:[/bold] {saved_path}")
    else:
        # Print to console if no output specified
        console.print(f"\n[bold]Transcription:[/bold]")
        console.print(result.text)


@cli.command()
@click.option("--duration", "-d", type=float, help="Recording duration in seconds")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
@click.option("--sample-rate", default=16000, help="Sample rate in Hz")
@click.option("--channels", default=1, help="Number of channels")
@click.option("--device", type=int, help="Audio device index")
@click.option("--transcribe", is_flag=True, help="Transcribe after recording")
@click.option("--model", "-m", default="base", help="Whisper model for transcription")
@click.pass_context
def record(ctx, duration, output, sample_rate, channels, device, transcribe, model):
    """Record audio from microphone."""
    # Initialize recorder
    recorder = AudioRecorder(
        sample_rate=sample_rate,
        channels=channels,
        device=device
    )
    
    # Show available devices if requested
    if device is None:
        devices = AudioRecorder.list_devices()
        if devices:
            console.print("\n[bold]Available audio devices:[/bold]")
            table = Table(show_header=True)
            table.add_column("Index", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Channels")
            
            for dev in devices:
                table.add_row(
                    str(dev['index']),
                    dev['name'],
                    str(dev['channels'])
                )
            
            console.print(table)
            console.print("\nUsing default device\n")
    
    # Start recording
    if duration:
        console.print(f"[bold blue]Recording for {duration} seconds...[/bold blue]")
        console.print("Press Ctrl+C to stop early\n")
        
        with Progress(console=console) as progress:
            task = progress.add_task("Recording...", total=duration)
            
            def update_progress(p):
                if duration:
                    progress.update(task, completed=p)
            
            try:
                audio_path = recorder.record(
                    output,
                    duration=duration,
                    callback=update_progress
                )
            except KeyboardInterrupt:
                recorder.stop()
                console.print("\n[yellow]Recording stopped by user[/yellow]")
    else:
        # Interactive recording
        audio_path = recorder.record_interactive(
            output_dir=Path(output).parent,
            prefix=Path(output).stem,
            format=Path(output).suffix[1:]
        )
    
    console.print(f"\n[bold green]✓ Recording saved:[/bold green] {audio_path}")
    console.print(f"Size: {format_size(Path(audio_path).stat().st_size)}")
    
    # Transcribe if requested
    if transcribe:
        console.print(f"\n[bold blue]Transcribing recording...[/bold blue]")
        
        transcriber = Transcriber(model=model)
        result = transcriber.transcribe(audio_path)
        
        # Save transcription next to audio
        transcript_path = Path(audio_path).with_suffix(".txt")
        result.save(transcript_path)
        
        console.print(f"\n[bold green]✓ Transcription saved:[/bold green] {transcript_path}")
        console.print(f"Words: {len(result.text.split()):,}")


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), required=True, help="Output directory")
@click.option("--model", "-m", default="base", help="Whisper model size")
@click.option("--format", "-f", default="txt", help="Output format")
@click.option("--pattern", "-p", default="*", help="File pattern (e.g., '*.mp3')")
@click.option("--recursive", "-r", is_flag=True, help="Process subdirectories")
@click.option("--num-workers", default=1, help="Number of parallel workers")
@click.pass_context
def batch(ctx, input_dir, output_dir, model, format, pattern, recursive, num_workers):
    """Process multiple audio files."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Find audio files
    if recursive:
        audio_files = list(input_path.rglob(pattern))
    else:
        audio_files = list(input_path.glob(pattern))
    
    # Filter to audio files
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus', '.webm'}
    audio_files = [f for f in audio_files if f.suffix.lower() in audio_extensions]
    
    if not audio_files:
        console.print(f"[red]No audio files found matching pattern: {pattern}[/red]")
        return
    
    console.print(f"\n[bold]Found {len(audio_files)} audio files[/bold]")
    
    # Initialize processor
    processor = BatchProcessor(
        model=model,
        output_format=format,
        num_workers=num_workers
    )
    
    # Process files
    with Progress(console=console) as progress:
        task = progress.add_task("Processing files...", total=len(audio_files))
        
        def update_progress(completed, total):
            progress.update(task, completed=completed)
        
        results = processor.process_files(
            audio_files,
            output_path,
            progress_callback=update_progress
        )
    
    # Show summary
    successful = len([r for r in results if r['success']])
    failed = len([r for r in results if not r['success']])
    
    console.print(f"\n[bold green]✓ Batch processing complete![/bold green]")
    console.print(f"Successful: {successful}")
    if failed > 0:
        console.print(f"[red]Failed: {failed}[/red]")
        
        # Show failed files
        for result in results:
            if not result['success']:
                console.print(f"  - {result['file']}: {result.get('error', 'Unknown error')}")


@cli.command()
@click.option("--list", "list_models", is_flag=True, help="List available models")
@click.option("--download", help="Download a specific model")
@click.option("--info", help="Show model information")
def models(list_models, download, info):
    """Manage Whisper models."""
    if list_models:
        console.print("\n[bold]Available Whisper Models:[/bold]\n")
        
        models_info = [
            ("tiny", "39M", "~1GB", "~32x", "17.4%"),
            ("base", "74M", "~1GB", "~16x", "12.6%"),
            ("small", "244M", "~2GB", "~6x", "9.5%"),
            ("medium", "769M", "~5GB", "~2x", "7.4%"),
            ("large", "1550M", "~10GB", "1x", "6.2%"),
        ]
        
        table = Table(show_header=True)
        table.add_column("Model", style="cyan")
        table.add_column("Parameters", style="green")
        table.add_column("Required VRAM")
        table.add_column("Relative Speed")
        table.add_column("WER (Word Error Rate)")
        
        for model_info in models_info:
            table.add_row(*model_info)
        
        console.print(table)
        
    elif download:
        console.print(f"\n[bold]Downloading model: {download}[/bold]")
        try:
            import whisper
            whisper.load_model(download)
            console.print(f"[green]✓ Model '{download}' downloaded successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to download model: {str(e)}[/red]")
    
    elif info:
        # Show detailed model information
        console.print(f"\n[bold]Model: {info}[/bold]")
        # Add more detailed information here


@cli.command()
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--set", "set_key", help="Set configuration key (format: key=value)")
@click.option("--file", type=click.Path(), help="Load configuration from file")
@click.pass_context
def config(ctx, show, set_key, file):
    """Manage configuration."""
    config = ctx.obj["config"]
    
    if show:
        console.print("\n[bold]Current Configuration:[/bold]")
        console.print(config.to_yaml())
    
    elif set_key:
        try:
            key, value = set_key.split("=", 1)
            config.set(key, value)
            console.print(f"[green]✓ Set {key} = {value}[/green]")
        except ValueError:
            console.print("[red]Invalid format. Use: key=value[/red]")
    
    elif file:
        try:
            config = Config.from_file(file)
            console.print(f"[green]✓ Loaded configuration from {file}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to load configuration: {str(e)}[/red]")


def main():
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if logger.isEnabledFor(logging.DEBUG):
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()