"""
fakenews-br-data: Brazilian fake news dataset collection, processing, and analysis toolkit.

This package provides tools for collecting, normalizing, cleaning, and analyzing
Brazilian Portuguese fake news datasets from multiple sources.
"""

__version__ = "0.1.0"

from .pipeline import Pipeline
from .cleaning import DatasetCleaner
from .deduplication import DuplicateDetector
from .factcheck import FactChecker
from .config import load_config, save_config
from .schema import ensure_schema, normalize_date
from .downloaders import (
    HuggingFaceDownloader,
    ZenodoDownloader,
    URLDownloader,
    LocalFileLoader,
)

__all__ = [
    "__version__",
    "Pipeline",
    "DatasetCleaner",
    "DuplicateDetector",
    "FactChecker",
    "load_config",
    "save_config",
    "ensure_schema",
    "normalize_date",
    "HuggingFaceDownloader",
    "ZenodoDownloader",
    "URLDownloader",
    "LocalFileLoader",
]

