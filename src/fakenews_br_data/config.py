"""Configuration management for fakenews-br-data package."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        raise ImportError("tomli or tomllib is required for TOML support")

try:
    import tomli_w
except ImportError:
    raise ImportError("tomli-w is required for writing TOML files")

load_dotenv()

DEFAULT_CONFIG_PATH = Path.home() / ".fakenews-br-data" / "config.toml"

DEFAULT_CONFIG = {
    "factcheck_api_key": "",
    "out_dir": "data",
    "max_workers": 31,
    "factcheck_sleep": 1.0,
    "max_inflight": 200,
    "min_tokens": 5,
    "max_query_size": 512,
    "language_code": "pt-BR",
    "show_progress_bar": True,
    "deduplication": {
        "threshold": 0.7,
        "ngram": 5,
        "seed": 3,
        "num_perm": 128,
        "bands": 50,
    },
}


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from TOML file and environment variables.
    
    Args:
        path: Path to config file. If None, tries default location first,
              then falls back to default config.
              
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    if path is None:
        if DEFAULT_CONFIG_PATH.exists():
            path = str(DEFAULT_CONFIG_PATH)
        else:
            path = None
    
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            user_config = tomli.load(f)
        config.update(user_config)
    
    factcheck_api_key = os.getenv("FACTCHECK_API_KEY")
    if factcheck_api_key:
        config["factcheck_api_key"] = factcheck_api_key
    
    return config


def save_config(config: Dict[str, Any], path: Optional[str] = None) -> None:
    """
    Save configuration to TOML file.
    
    Args:
        config: Configuration dictionary
        path: Path to save to. If None, uses default location.
    """
    if path is None:
        path = str(DEFAULT_CONFIG_PATH)
        DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "wb") as f:
        tomli_w.dump(config, f)

