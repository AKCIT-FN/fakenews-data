"""Dataset downloaders from various sources."""

import os
import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datasets import load_dataset
from fakenews_br_data.utils import download_to


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
    
    def __init__(self, dataset: str, subset: Optional[str], name: str):
        """
        Initialize HuggingFaceDownloader.

        Args:
            dataset: Hugging Face dataset identifier (e.g., 'ju-resplande/portuguese-fact-checking').
            subset: Optional subset/config name (e.g., 'Fake.br_raw').
            name: Local name for saving the dataset file.
        """
        self.dataset = dataset
        self.subset = subset
        self.name = name
    
    def download(self, output_dir: str) -> List[str]:
        """Download Hugging Face dataset and save as Parquet."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{self.name}.parquet")

        if os.path.exists(path) and os.path.getsize(path) > 0:
            logging.info(f"Skipping existing HuggingFace dataset: {self.name}")
            return [path]

        try:
            logging.info(f"Downloading HuggingFace dataset: {self.dataset} ({self.subset or 'default'})")

            if self.subset:
                ds = load_dataset(self.dataset, self.subset)
            else:
                ds = load_dataset(self.dataset)

            split_name = next(iter(ds.keys()))
            df = ds[split_name].to_pandas()
            df.to_parquet(path, index=False)

            logging.info(f"Saved HuggingFace dataset: {self.name} ({len(df)} records)")
            return [path]

        except Exception as e:
            logging.error(f"Failed to download HuggingFace dataset '{self.dataset}' ({self.subset}): {e}")
            raise RuntimeError(f"Failed to download {self.dataset} ({self.subset}): {e}") from e


class ZenodoDownloader(BaseDownloader):
    """Download datasets from Zenodo records."""

    def __init__(self, record_id: int, file_filters: Optional[List[str]] = None):
        """
        Initialize ZenodoDownloader.

        Args:
            record_id: Zenodo record ID.
            file_filters: List of filenames to download (if None, downloads all).
        """
        self.record_id = record_id
        self.file_filters = file_filters or []
    
    def _get_files(self) -> List[Dict]:
        """Fetch the list of files available in the Zenodo record."""
        api_url = f"https://zenodo.org/api/records/{self.record_id}"
        r = requests.get(api_url, timeout=60)
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
        """Download one or more files from a Zenodo record."""
        os.makedirs(output_dir, exist_ok=True)
        files = self._get_files()
        downloaded_paths = []

        for f in files:
            filename = f.get("key") or f.get("filename", "")
            if self.file_filters and filename not in self.file_filters:
                continue

            link = f.get("links", {}).get("self") or f.get("links", {}).get("download", "")
            if not link:
                continue

            local_path = os.path.join(output_dir, f"Zenodo{self.record_id}__{filename}")
            logging.info(f"Downloading from Zenodo: {filename}")
            download_to(local_path, link)
            downloaded_paths.append(local_path)

        logging.info(f"Downloaded {len(downloaded_paths)} file(s) from Zenodo record {self.record_id}")
        return downloaded_paths


class LocalFileLoader(BaseDownloader):
    """Load datasets from existing local files."""

    def __init__(self, source_files: Dict[str, Dict[str, str]]):
        """
        Initialize LocalFileLoader.

        Args:
            source_files: Dict mapping file paths to metadata dicts.
        """
        self.source_files = source_files

    def download(self, output_dir: str) -> List[str]:
        """Copy local files to the output directory."""
        os.makedirs(output_dir, exist_ok=True)
        copied_paths = []

        for filename in self.source_files:
            if os.path.exists(filename):
                dest = os.path.join(output_dir, os.path.basename(filename))
                if os.path.abspath(filename) != os.path.abspath(dest):
                    with open(filename, "rb") as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                copied_paths.append(dest)
                logging.info(f"Copied local file: {os.path.basename(filename)}")

        return copied_paths

class URLDownloader(BaseDownloader):
    """Download datasets from direct URLs (e.g., GitHub raw, CSV links)."""

    def __init__(self, url: str, filename: str):
        """
        Initialize URLDownloader.

        Args:
            url: Direct URL to the file (should be a raw link if GitHub).
            filename: Local filename to save as.
        """
        self.url = url
        self.filename = filename

    def download(self, output_dir: str) -> List[str]:
        """Download file from a direct URL."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, self.filename)

        logging.info(f"Downloading from URL: {self.url}")
        download_to(path, self.url)
        logging.info(f"Saved file: {os.path.basename(path)}")

        return [path]
    
try:
    from kaggle.api.kaggle_api_extended import KaggleApi

    class KaggleDownloader(BaseDownloader):
        """Download datasets from Kaggle (requires kaggle.json credentials)."""

        def __init__(self, dataset: str, file_filters: Optional[List[str]] = None):
            """
            Initialize KaggleDownloader.

            Args:
                dataset: Kaggle dataset identifier (e.g., 'fabioselau/fakes-news-portuguese').
                file_filters: Optional list of files to keep after unzip.
            """
            self.dataset = dataset
            self.file_filters = file_filters or []

        def download(self, output_dir: str) -> List[str]:
            """Download and extract dataset from Kaggle."""
            os.makedirs(output_dir, exist_ok=True)
            api = KaggleApi()
            api.authenticate()

            logging.info(f"Downloading Kaggle dataset: {self.dataset}")
            api.dataset_download_files(self.dataset, path=output_dir, unzip=True)

            all_files = os.listdir(output_dir)
            selected = (
                [os.path.join(output_dir, f) for f in all_files if f in self.file_filters]
                if self.file_filters
                else [os.path.join(output_dir, f) for f in all_files]
            )

            logging.info(f"Downloaded {len(selected)} Kaggle file(s) from {self.dataset}")
            return selected

except ImportError:
    class KaggleDownloader(BaseDownloader):
        """Fallback stub when Kaggle API is not available."""
        def __init__(self, *args, **kwargs):
            raise ImportError("KaggleDownloader requires the 'kaggle' package to be installed.")
