"""Command-line interface for fakenews-br-data."""

from typing import Optional, List
import typer
from pydantic import BaseModel, field_validator
from loguru import logger

from .pipeline import Pipeline
from .cleaning import DatasetCleaner
from .factcheck import FactChecker
from .config import load_config

app = typer.Typer(help="Brazilian fake news dataset toolkit")

ALLOWED_TAGS = {
    "factcheck_api_key": str,
    "out_dir": str,
    "max_workers": int,
    "factcheck_sleep": float,
    "max_query_size": int,
    "language_code": str,
    "show_progress_bar": bool,
}


class ConfigOverride(BaseModel):
    """Pydantic model for config tag overrides."""
    
    factcheck_api_key: Optional[str] = None
    out_dir: Optional[str] = None
    max_workers: Optional[int] = None
    factcheck_sleep: Optional[float] = None
    max_query_size: Optional[int] = None
    language_code: Optional[str] = None
    show_progress_bar: Optional[bool] = None

    @field_validator("factcheck_sleep")
    @classmethod
    def validate_sleep(cls, v):
        if v is not None and v < 0:
            raise ValueError("factcheck_sleep must be >= 0")
        return v

    @field_validator("max_workers")
    @classmethod
    def validate_workers(cls, v):
        if v is not None and v < 1:
            raise ValueError("max_workers must be >= 1")
        return v


def _parse_tags(tags: List[str]) -> dict:
    """Parse tag overrides from command line."""
    result = {}
    for item in tags:
        if "=" not in item:
            raise typer.BadParameter(f"Invalid tag format: {item}. Expected key=value")
        k, v = item.split("=", 1)
        if k not in ALLOWED_TAGS:
            raise typer.BadParameter(f"Unknown tag: {k}. Allowed: {list(ALLOWED_TAGS.keys())}")
        typ = ALLOWED_TAGS[k]
        try:
            if typ is bool:
                result[k] = v.lower() in ("true", "1", "yes", "on")
            else:
                result[k] = typ(v)
        except ValueError as e:
            raise typer.BadParameter(f"Invalid value for {k}: {v} ({e})")
    return result


def _merge_config(config_path: Optional[str], tags: List[str]) -> dict:
    """Load config and apply tag overrides."""
    base = load_config(config_path) if config_path else {}
    tag_overrides = _parse_tags(tags) if tags else {}
    base.update(tag_overrides)
    return base


@app.command()
def pipeline(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration TOML file"),
    tag: List[str] = typer.Option([], "--tag", "-t", help="Override config values: key=value"),
    skip_download: bool = typer.Option(False, "--skip-download", help="Skip download step"),
):
    """Run full pipeline (download, process, clean, factcheck)."""
    try:
        cfg = _merge_config(config, tag)
        pipeline_instance = Pipeline(config=cfg)
        pipeline_instance.run_full_pipeline(skip_download=skip_download)
        logger.info("\nPipeline completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise typer.Exit(1)


@app.command()
def download(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration TOML file"),
    tag: List[str] = typer.Option([], "--tag", "-t", help="Override config values: key=value"),
):
    """Download datasets only."""
    try:
        cfg = _merge_config(config, tag)
        pipeline_instance = Pipeline(config=cfg)
        paths = pipeline_instance.download()
        logger.info(f"\nDownloaded {len(paths)} files")
        return 0
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise typer.Exit(1)


@app.command()
def process(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration TOML file"),
    tag: List[str] = typer.Option([], "--tag", "-t", help="Override config values: key=value"),
):
    """Normalize and merge datasets."""
    try:
        cfg = _merge_config(config, tag)
        pipeline_instance = Pipeline(config=cfg)
        df, _ = pipeline_instance.normalize_and_merge()
        pipeline_instance.save_merged(df)
        logger.info("\nDatasets merged successfully!")
        return 0
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise typer.Exit(1)


@app.command()
def clean(
    input: str = typer.Option(..., "--input", "-i", help="Input file path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration TOML file"),
):
    """Clean dataset."""
    try:
        cfg = load_config(config) if config else {}
        min_tokens = cfg.get("min_tokens", 5)
        
        cleaner = DatasetCleaner(min_tokens=min_tokens)
        
        output_csv = output or "FakenewsBR_clean.csv"
        output_parquet = output_csv.replace(".csv", ".parquet")
        
        cleaner.clean_dataset(input, output_csv, output_parquet)
        logger.info("\nCleaning completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        raise typer.Exit(1)


@app.command()
def factcheck(
    input: str = typer.Option(..., "--input", "-i", help="Input file path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    config: str = typer.Option(..., "--config", "-c", help="Path to configuration TOML file"),
    tag: List[str] = typer.Option([], "--tag", "-t", help="Override config values: key=value"),
):
    """Run Google Fact Check."""
    try:
        cfg = _merge_config(config, tag)
        api_key = cfg.get("factcheck_api_key")
        
        if not api_key:
            logger.error("Error: factcheck_api_key not set in configuration or environment")
            raise typer.Exit(1)
        
        checker = FactChecker(
            api_key=api_key,
            max_workers=cfg.get("max_workers", 31),
            max_inflight=cfg.get("max_inflight", 200),
            sleep_time=cfg.get("factcheck_sleep", 1.0),
            max_query_size=cfg.get("max_query_size", 512),
            language_code=cfg.get("language_code", "pt-BR"),
            show_progress_bar=cfg.get("show_progress_bar", True),
        )
        
        output_path = output or "FakenewsBR_factchecked.csv"
        output_dir = cfg.get("out_dir", "data")
        
        checker.process_dataset(input, output_path, output_dir)
        logger.info("\nFact checking completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Fact check failed: {e}")
        raise typer.Exit(1)


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
