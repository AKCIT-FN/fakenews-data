"""Dataset downloaders from various sources."""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from datasets import load_dataset
from .utils import download_to


class BaseDownloader(ABC):
    """Abstract base class for dataset downloaders."""
    
    @abstractmethod
    def download(self, output_dir: str) -> List[str]:
        """
        Download dataset to output directory.
        
        Args:
            output_dir: Directory to save files
            
        Returns:
            List of paths to downloaded files
        """
        pass


class HuggingFaceDownloader(BaseDownloader):
    """Download datasets from HuggingFace."""
    
    def __init__(self, dataset: str, subset: str, name: str):
        """
        Initialize HuggingFaceDownloader.
        
        Args:
            dataset: HuggingFace dataset identifier
            subset: Dataset subset name
            name: Local name for the dataset
        """
        self.dataset = dataset
        self.subset = subset
        self.name = name
    
    def download(self, output_dir: str) -> List[str]:
        """Download HuggingFace dataset as Parquet."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{self.name}.parquet")
        
        if not os.path.exists(path):
            ds = load_dataset(self.dataset, self.subset, split="train")
            ds.to_pandas().to_parquet(path, index=False)
        
        return [path]


class ZenodoDownloader(BaseDownloader):
    """Download datasets from Zenodo records."""
    
    def __init__(self, record_id: int, file_filters: Optional[List[str]] = None):
        """
        Initialize ZenodoDownloader.
        
        Args:
            record_id: Zenodo record ID
            file_filters: List of filenames to download (if None, downloads all)
        """
        self.record_id = record_id
        self.file_filters = file_filters or []
    
    def _get_files(self) -> List[Dict]:
        """Get list of files from Zenodo API."""
        api = f"https://zenodo.org/api/records/{self.record_id}"
        r = requests.get(api, timeout=60)
        r.raise_for_status()
        return r.json().get("files", [])
    
    def download(self, output_dir: str) -> List[str]:
        """Download files from Zenodo record."""
        os.makedirs(output_dir, exist_ok=True)
        files = self._get_files()
        paths = []
        
        for f in files:
            fname = f.get("key") or f.get("filename", "")
            if self.file_filters and fname not in self.file_filters:
                continue
            
            link = f.get("links", {}).get("self") or f.get("links", {}).get("download", "")
            if not link:
                continue
            
            local = os.path.join(output_dir, f"Zenodo{self.record_id}__{fname}")
            download_to(local, link)
            paths.append(local)
        
        return paths


class LocalFileLoader(BaseDownloader):
    """Load datasets from local files."""
    
    def __init__(self, source_files: Dict[str, Dict[str, str]]):
        """
        Initialize LocalFileLoader.
        
        Args:
            source_files: Dict mapping filenames to metadata dicts
        """
        self.source_files = source_files
    
    def download(self, output_dir: str) -> List[str]:
        """Copy local files to output directory."""
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        
        for filename in self.source_files:
            if os.path.exists(filename):
                dest = os.path.join(output_dir, os.path.basename(filename))
                if os.path.abspath(filename) != os.path.abspath(dest):
                    with open(filename, "rb") as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                paths.append(dest)
        
        return paths


class URLDownloader(BaseDownloader):
    """Download datasets from direct URLs."""
    
    def __init__(self, url: str, filename: str):
        """
        Initialize URLDownloader.
        
        Args:
            url: URL to download from
            filename: Local filename to save as
        """
        self.url = url
        self.filename = filename
    
    def download(self, output_dir: str) -> List[str]:
        """Download file from URL."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, self.filename)
        download_to(path, self.url)
        return [path]

