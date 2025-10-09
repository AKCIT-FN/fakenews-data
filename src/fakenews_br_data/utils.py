"""Utility functions for fakenews-br-data package."""

import hashlib
import json
import os
from typing import Dict
import requests


def sha256(path: str) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        path: Path to the file
        
    Returns:
        Hexadecimal hash string
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_manifest(folder: str) -> None:
    """
    Save a manifest.json file with SHA256 hashes and sizes of all files in folder.
    
    Args:
        folder: Directory path to scan
    """
    man = {}
    for fn in sorted(os.listdir(folder)):
        p = os.path.join(folder, fn)
        if os.path.isfile(p) and fn != "manifest.json":
            man[fn] = {"sha256": sha256(p), "bytes": os.path.getsize(p)}
    with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2, ensure_ascii=False)


def download_to(path: str, url: str) -> str:
    """
    Download a file from URL to local path.
    
    Args:
        path: Local file path to save to
        url: URL to download from
        
    Returns:
        Path to downloaded file
        
    Raises:
        requests.HTTPError: If download fails
    """
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path

