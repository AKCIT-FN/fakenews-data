"""Utility functions for fakenews-br-data package."""

import hashlib
import json
import logging
import os
import time
import requests
from typing import Dict, Optional
from datetime import datetime

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


def download_to(path: str, url: str, max_retries: int = 3, sleep: float = 3.0) -> str:
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
    log_path = os.path.join(os.path.dirname(path), "download_log.txt")

    def _log(status: str, message: str):
        """Append concise log entry to download_log.txt"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as logf:
            logf.write(f"[{ts}] {status} | {os.path.basename(path)} | {message}\n")

    if os.path.exists(path):
        size = os.path.getsize(path)
        if size >= min_file_size:
            logging.info(f"[Download] Skipping existing valid file: {os.path.basename(path)} ({size/1e6:.2f} MB)")
            _log("SKIP", f"Existing valid file ({size/1e6:.2f} MB)")
            return path
        else:
            logging.warning(f"[Download] Re-downloading {os.path.basename(path)} (size too small: {size} bytes)")
            try:
                os.remove(path)
            except OSError:
                pass

    # Download loop with retries
    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, stream=True, timeout=120, allow_redirects=True) as r:
                r.raise_for_status()

                content_type = r.headers.get("Content-Type", "")
                if "text/html" in content_type.lower():
                    raise RuntimeError(f"Unexpected HTML response ({content_type})")

                total_size = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                # Validate completeness
                if total_size and downloaded < total_size * 0.95:
                    raise IOError("Incomplete download (less than 95% of expected size)")

                logging.info(f"[Download] OK | {os.path.basename(path)} | {downloaded/1e6:.2f} MB from {url}")
                _log("OK", f"{downloaded/1e6:.2f} MB from {url}")
                return path

        except Exception as e:
            if attempt < max_retries:
                wait = sleep * (2 ** (attempt - 1))
                logging.warning(f"[Download] Attempt {attempt}/{max_retries} failed ({e}). Retrying in {wait:.1f}s...")
                _log("RETRY", f"Attempt {attempt} failed: {e}")
                time.sleep(wait)
            else:
                logging.error(f"[Download] FAILED after {max_retries} attempts: {url}")
                _log("FAIL", str(e))
                raise RuntimeError(f"Failed to download {url}: {e}") from e

