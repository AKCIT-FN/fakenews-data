"""Dataset downloaders from various sources."""

import os
import requests
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datasets import load_dataset
from tqdm.auto import tqdm
from loguru import logger

try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except ImportError:
    KaggleApi = None

from fakenews_br_data.utils import download_to


class BaseDownloader(ABC):
    """Abstract base class for dataset downloaders."""
    
    @abstractmethod
    def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
        """
        Download dataset to output directory.
        
        Args:
            output_dir: Directory to save files
            show_progress_bar: Whether to show progress bar
            
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
    
    def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
        """Download Hugging Face dataset and save as Parquet."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{self.name}.parquet")

        if os.path.exists(path) and os.path.getsize(path) > 0:
            logger.info(f"[HF] Skipping existing dataset: {self.name}")
            return [path]

        try:
            logger.info(f"[HF] Downloading dataset: {self.dataset} ({self.subset or 'default'})")

            subset_fixed = None
            if self.subset:
                subset_fixed = self.subset.strip().replace(" (raw)", "_raw")

            ds = load_dataset(self.dataset, subset_fixed) if subset_fixed else load_dataset(self.dataset)
            split_name = next(iter(ds.keys()))
            df = ds[split_name].to_pandas()
            df.to_parquet(path, index=False)

            logger.info(f"[HF] download completed {self.name}: {len(df)} records saved in {path}")
            return [path]

        except Exception as e:
            logger.error(f"[HF] Failed to download '{self.dataset}' ({self.subset}): {e}")
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
    
    def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
        """Download files from Zenodo record."""
        dataset_dir = os.path.join(output_dir, f"Zenodo_{self.record_id}")
        os.makedirs(output_dir, exist_ok=True)
        files = self._get_files()
        paths = []
        
        pbar = tqdm(files, desc="Downloading from Zenodo", disable=not show_progress_bar)
        for f in pbar:
            fname = f.get("key") or f.get("filename", "")
            if self.file_filters and fname not in self.file_filters:
                continue
            
            link = f.get("links", {}).get("self") or f.get("links", {}).get("download", "")
            if not link:
                continue
            
            local_path = os.path.join(dataset_dir, fname)
            pbar.set_description(f"Downloading {fname}")
            logger.info(f"[Zenodo]: {fname}")
            download_to(local_path, link)
            paths.append(local_path)
        pbar.close()
        
        logger.info(f"[Zenodo]: {len(paths)} files downloaded from {self.record_id}")
        return paths


class LocalFileLoader(BaseDownloader):
    """Load datasets from existing local files."""

    def __init__(self, source_files: Dict[str, Dict[str, str]]):
        """
        Initialize LocalFileLoader.

        Args:
            source_files: Dict mapping file paths to metadata dicts.
        """
        self.source_files = source_files

    def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
        """Copy local files to the output directory."""
        os.makedirs(output_dir, exist_ok=True)
        copied_paths = []

        file_list = list(self.source_files.keys())
        pbar = tqdm(file_list, desc="Copying local files", disable=not show_progress_bar)
        for filename in pbar:
            if os.path.exists(filename):
                dest_dir = os.path.join(output_dir, "local_files")
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, os.path.basename(filename))
                if os.path.abspath(filename) != os.path.abspath(dest):
                    with open(filename, "rb") as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                copied_paths.append(dest)
                pbar.set_description(f"Copying {os.path.basename(filename)}")
                logger.info(f"[Local] Copied: {os.path.basename(filename)} → {dest}")
            else:
                logger.warning(f"[Local] File not found: {filename}")
        pbar.close()

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

    def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
        """Download file from a direct URL with retry, exponential backoff, and optional GitHub auth."""

        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, self.filename)

        max_retries = 5  
        base_delay = 3
        headers = {}

        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
            logger.info("Using GitHub token for authentication.")
        else:
            logger.warning("No GitHub token found. You may hit rate limits (HTTP 429).")

        pbar = tqdm(total=max_retries, desc=f"Downloading {self.filename}", disable=not show_progress_bar)
        for attempt in range(max_retries):
            try:
                delay = random.uniform(1, 3)
                logger.info(f"Waiting {delay:.1f}s before downloading {self.filename} (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)

                logger.info(f"Downloading from URL: {self.url}")
                response = requests.get(self.url, headers=headers, timeout=60)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", base_delay * (2 ** attempt)))
                    logger.warning(f"429 Too Many Requests. Retrying in {retry_after}s...")
                    time.sleep(retry_after)
                    pbar.update(1)
                    continue

                response.raise_for_status()

                with open(path, "wb") as f:
                    f.write(response.content)

                logger.info(f"[URL]: {self.filename} (trying to download {self.url})")
                result = download_to(path, self.url)
                logger.info(f"[URL]: {self.filename} saved in {result}")
                pbar.close()
                return [result]

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = base_delay * (2 ** attempt)
                    logger.warning(f"Download attempt {attempt + 1} failed ({e}). Retrying in {wait}s...")
                    time.sleep(wait)
                    pbar.update(1)
                else:
                    pbar.close()
                    logger.error(f"Failed to download {self.url} after {max_retries} attempts: {e}")
                    raise RuntimeError(f"Failed to download {self.url}: {e}") from e

try:

    class KaggleDownloader(BaseDownloader):
        """Download datasets from Kaggle (using direct API key or environment variables)."""

        def __init__(self, dataset: str, file_filters: Optional[List[str]] = None):
            """
            Initialize KaggleDownloader.

            Args:
                dataset: Kaggle dataset identifier.
                file_filters: Optional list of files to keep after unzip.
            """
            self.dataset = dataset
            self.file_filters = file_filters or []

        def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
            """Download and extract dataset from Kaggle"""
            if KaggleApi is None:
                raise ImportError("KaggleDownloader requires the 'kaggle' package to be installed.")
            
            os.makedirs(output_dir, exist_ok=True)

            username = os.getenv("KAGGLE_USERNAME")
            key = os.getenv("KAGGLE_KEY")

            if not username or not key:
                logger.error("[Kaggle] Missing Kaggle credentials. Please set KAGGLE_USERNAME and KAGGLE_KEY environment variables.")
                raise RuntimeError("Kaggle credentials not found in environment variables.")

            logger.info(f"Using Kaggle credentials from environment (user: {username})")

            api = KaggleApi()
            api.authenticate()
            api.config_values = {
                "username": username,
                "key": key,
                "path": os.path.expanduser("~/.kaggle"),
            }

            try:
                api.authenticate()
                logger.info("[Kaggle]: Authenticated successfully with Kaggle API")
            except Exception as e:
                logger.error(f"[Kaggle]: Kaggle authentication failed: {e}")
                raise RuntimeError(f"Kaggle authentication failed: {e}") from e

            max_retries = 5
            base_delay = 3

            pbar = tqdm(total=max_retries, desc=f"Downloading {self.dataset}", disable=not show_progress_bar)
            for attempt in range(max_retries):
                try:
                    delay = random.uniform(1, 3)
                    logger.info(f"[Kaggle]: Waiting {delay:.1f}s before downloading from Kaggle (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)

                    logger.info(f"[Kaggle]: Downloading dataset: {self.dataset}")
                    api.dataset_download_files(self.dataset, path=output_dir, unzip=True)
                    pbar.close()
                    break 

                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = base_delay * (2 ** attempt)
                        logger.warning(f"[Kaggle]: Attempt {attempt + 1} failed ({e}). Retrying in {wait}s...")
                        time.sleep(wait)
                        pbar.update(1)
                    else:
                        pbar.close()
                        logger.error(f"[Kaggle]: Failed to download Kaggle dataset '{self.dataset}' after {max_retries} attempts: {e}")
                        raise RuntimeError(f"Failed to download Kaggle dataset: {e}") from e

            all_files = os.listdir(output_dir)
            selected = (
                [os.path.join(output_dir, f) for f in all_files if f in self.file_filters]
                if self.file_filters
                else [os.path.join(output_dir, f) for f in all_files]
            )

            logger.info(f"[Kaggle]: Downloaded {len(selected)} Kaggle file(s) from {self.dataset}")
            return selected

except ImportError:
    class KaggleDownloader(BaseDownloader):
        """Fallback stub when Kaggle API is not available."""
        def __init__(self, *args, **kwargs):
            raise ImportError("KaggleDownloader requires the 'kaggle' package to be installed.")
        
        def download(self, output_dir: str, show_progress_bar: bool = True) -> List[str]:
            raise ImportError("KaggleDownloader requires the 'kaggle' package to be installed.")

