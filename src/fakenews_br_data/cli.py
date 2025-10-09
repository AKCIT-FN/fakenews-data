"""Command-line interface for fakenews-br-data."""

import argparse
import sys
from typing import Optional
from .pipeline import Pipeline
from .cleaning import DatasetCleaner
from .factcheck import FactChecker
from .config import load_config


def cmd_pipeline(args):
    """Run full pipeline."""
    pipeline = Pipeline(config_path=args.config)
    results = pipeline.run_full_pipeline(skip_download=args.skip_download)
    print("\nPipeline completed successfully!")
    return 0


def cmd_download(args):
    """Download datasets only."""
    pipeline = Pipeline(config_path=args.config)
    paths = pipeline.download()
    print(f"\nDownloaded {len(paths)} files")
    return 0


def cmd_process(args):
    """Normalize and merge datasets."""
    pipeline = Pipeline(config_path=args.config)
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
    config = load_config(args.config)
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
        "--skip-download",
        action="store_true",
        help="Skip download step (use existing files)",
    )
    parser_pipeline.set_defaults(func=cmd_pipeline)
    
    parser_download = subparsers.add_parser("download", help="Download datasets only")
    parser_download.add_argument(
        "--config", type=str, help="Path to configuration JSON file"
    )
    parser_download.set_defaults(func=cmd_download)
    
    parser_process = subparsers.add_parser(
        "process", help="Normalize and merge datasets"
    )
    parser_process.add_argument(
        "--config", type=str, help="Path to configuration JSON file"
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
    parser_factcheck.set_defaults(func=cmd_factcheck)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

