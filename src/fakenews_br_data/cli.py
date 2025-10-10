"""Command-line interface for fakenews-br-data."""

import argparse
import sys
from typing import Optional
from .pipeline import Pipeline
from .cleaning import DatasetCleaner
from .factcheck import FactChecker
from .config import load_config
import json, tempfile
from pathlib import Path

# chaves permitidas para --tag com tipagem rígida
ALLOWED = {
    "factcheck_api_key": str,
    "out_dir": str,
    "max_workers": int,
    "factcheck_sleep": int,
}

def _apply_tags(cfg: dict, tags: list[str] | None) -> dict:
    if not tags:
        return cfg
    for item in tags:
        if "=" not in item:
            raise ValueError(f"tag inválida: {item}")
        k, v = item.split("=", 1)
        if k not in ALLOWED:
            raise ValueError(f"chave não permitida: {k}")
        typ = ALLOWED[k]
        cfg[k] = typ(v)
    return cfg

def _merged_config_path(config_path: Optional[str], tags: list[str] | None) -> str:
    """Carrega config (se houver), aplica --tag e grava JSON temporário. Retorna o caminho."""
    base = load_config(config_path) if config_path else {}
    merged = _apply_tags(base, tags)
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(merged, tf, ensure_ascii=False, indent=2)
    tf.flush(); tf.close()
    return tf.name


def cmd_pipeline(args):
    """Run full pipeline."""
    cfg_path = _merged_config_path(args.config, args.tag)
    pipeline = Pipeline(config_path=cfg_path)
    results = pipeline.run_full_pipeline(skip_download=args.skip_download)
    print("\nPipeline completed successfully!")
    return 0


def cmd_download(args):
    """Download datasets only."""
    cfg_path = _merged_config_path(args.config, args.tag)
    pipeline = Pipeline(config_path=cfg_path)
    paths = pipeline.download()
    print(f"\nDownloaded {len(paths)} files")
    return 0


def cmd_process(args):
    """Normalize and merge datasets."""
    cfg_path = _merged_config_path(args.config, args.tag)
    pipeline = Pipeline(config_path=cfg_path)
    df = pipeline.normalize_and_merge()
    pipeline.save_merged(df)
    print("\nDatasets merged successfully!")
    return 0


def cmd_clean(args):
    """Clean dataset."""
    if args.config:
        config = load_config(args.config)
        min_tokens = config.get("min_tokens", 5)
    else:
        min_tokens = 5
    
    cleaner = DatasetCleaner(min_tokens=min_tokens)
    
    output_csv = args.output or "FakenewsBR_clean.csv"
    output_parquet = output_csv.replace(".csv", ".parquet")
    
    cleaner.clean_dataset(args.input, output_csv, output_parquet)
    print("\nCleaning completed successfully!")
    return 0


def cmd_factcheck(args):
    """Run fact checking."""
    config = _apply_tags(load_config(args.config), args.tag)
    api_key = config.get("factcheck_api_key")
    
    if not api_key:
        print("Error: factcheck_api_key not set in configuration", file=sys.stderr)
        return 1
    
    checker = FactChecker(
        api_key=api_key,
        max_workers=config.get("max_workers", 31),
        max_inflight=config.get("max_inflight", 200),
        sleep_time=config.get("factcheck_sleep", 1.0),
    )
    
    output = args.output or "FakenewsBR_factchecked.csv"
    output_dir = config.get("out_dir", "data")
    
    checker.process_dataset(args.input, output, output_dir)
    print("\nFact checking completed successfully!")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Brazilian fake news dataset toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    parser_pipeline = subparsers.add_parser(
        "pipeline", help="Run full pipeline (download, process, clean, factcheck)"
    )
    parser_pipeline.add_argument(
        "--config", type=str, help="Path to configuration JSON file"
    )
    parser_pipeline.add_argument(
        "--tag", action="append", default=[], help="Overrides: factcheck_api_key=..., out_dir=..., max_workers=..., factcheck_sleep=..."
    )
    parser_pipeline.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download step (use existing files)",
    )
    parser_pipeline.set_defaults(func=cmd_pipeline)
    
    parser_download = subparsers.add_parser("download", help="Download datasets only")
    parser_download.add_argument(
        "--config", type=str, help="Path to configuration JSON file"
    )
    parser_download.add_argument(
        "--tag", action="append", default=[], help="Overrides permitidos"
    )
    parser_download.set_defaults(func=cmd_download)
    
    parser_process = subparsers.add_parser(
        "process", help="Normalize and merge datasets"
    )
    parser_process.add_argument(
        "--config", type=str, help="Path to configuration JSON file"
    )
    parser_process.add_argument(
        "--tag", action="append", default=[], help="Overrides permitidos"
    )
    parser_process.set_defaults(func=cmd_process)
    
    parser_clean = subparsers.add_parser("clean", help="Clean dataset")
    parser_clean.add_argument("--input", type=str, required=True, help="Input file path")
    parser_clean.add_argument("--output", type=str, help="Output file path")
    parser_clean.add_argument("--config", type=str, help="Path to configuration JSON file")
    parser_clean.set_defaults(func=cmd_clean)
    
    parser_factcheck = subparsers.add_parser(
        "factcheck", help="Run Google Fact Check"
    )
    parser_factcheck.add_argument(
        "--input", type=str, required=True, help="Input file path"
    )
    parser_factcheck.add_argument("--output", type=str, help="Output file path")
    parser_factcheck.add_argument(
        "--config", type=str, required=True, help="Path to configuration JSON file"
    )
    parser_factcheck.add_argument(
        "--tag", action="append", default=[], help="Overrides permitidos"
    )
    parser_factcheck.set_defaults(func=cmd_factcheck)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

