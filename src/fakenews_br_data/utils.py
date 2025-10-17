"""Utility functions for fakenews-br-data package."""

import hashlib
import json
import logging
import os
import time
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
    Save a manifest.json file with SHA256 hashes and sizes of all files in the folder.
    
    Args:
        folder: Directory path to scan.
    """
    manifest = {}
    for fn in sorted(os.listdir(folder)):
        full_path = os.path.join(folder, fn)
        if os.path.isfile(full_path) and fn != "manifest.json":
            manifest[fn] = {
                "sha256": sha256(full_path),
                "bytes": os.path.getsize(full_path),
            }
    
    manifest_path = os.path.join(folder, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Manifest saved at: {manifest_path}")


def download_to(path: str, url: str, max_retries: int = 3, sleep: float = 2.0) -> str:
    """
    Download a file from a URL to a local path (with retries, streaming, and skip if exists).
    
    Args:
        path: Local file path to save to.
        url: URL to download from.
        max_retries: Number of retries on failure (default: 3).
        sleep: Seconds to wait between retries (default: 2.0).
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        RuntimeError: If download fails after all retries.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path) and os.path.getsize(path) > 0:
        logging.info(f"⚙️ Skipping existing file: {os.path.basename(path)}")
        return path

    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, stream=True, timeout=120, allow_redirects=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                if total_size and downloaded < total_size * 0.95:
                    raise IOError("Incomplete download (less than 95% of expected size)")

                logging.info(
                    f"Downloaded {os.path.basename(path)} "
                    f"({downloaded/1e6:.2f} MB) from {url}"
                )
                return path

        except Exception as e:
            logging.warning(
                f"Attempt {attempt}/{max_retries} failed for {url}: {e}"
            )
            time.sleep(sleep)

    raise RuntimeError(f"Failed to download {url} after {max_retries} retries")

