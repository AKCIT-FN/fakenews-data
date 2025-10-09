"""Configuration management for fakenews-br-data package."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG_PATH = Path.home() / ".fakenews-br-data" / "config.json"

DEFAULT_CONFIG = {
    "factcheck_api_key": "",
    "out_dir": "data",
    "max_workers": 31,
    "factcheck_sleep": 1,
    "max_inflight": 200,
    "min_tokens": 5,
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
    Load configuration from JSON file.
    
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
            return config
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        user_config = json.load(f)
    
    config.update(user_config)
    return config


def save_config(config: Dict[str, Any], path: Optional[str] = None) -> None:
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary
        path: Path to save to. If None, uses default location.
    """
    if path is None:
        path = str(DEFAULT_CONFIG_PATH)
        DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

