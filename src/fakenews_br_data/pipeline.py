"""Main pipeline orchestration for dataset processing."""

import os
import logging
from typing import List, Optional, Dict, Any
import pandas as pd

from fakenews_br_data.config import load_config
from fakenews_br_data.downloaders import (
    HuggingFaceDownloader,
    ZenodoDownloader,
    URLDownloader,
    LocalFileLoader,
    KaggleDownloader,
)
from fakenews_br_data.schema import ensure_schema, assign_uids, extract_tweet_id
from fakenews_br_data.cleaning import DatasetCleaner
from fakenews_br_data.deduplication import DuplicateDetector
from fakenews_br_data.factcheck import FactChecker
from fakenews_br_data.utils import save_manifest


class Pipeline:
    """
    Complete pipeline for dataset download, normalization, cleaning, and fact-checking.
    """
    
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Pipeline.
        
        Args:
            config_path: Path to configuration JSON file.
            config: Configuration dictionary (overrides config_path).
        """
        if config is not None:
            self.config = config
        else:
            self.config = load_config(config_path)

        self.out_dir = self.config.get("out_dir", "data")
        self.raw_dir = os.path.join(self.out_dir, "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

        self.downloaders = self._setup_downloaders()
    
    def _setup_downloaders(self) -> List:
        """Setup dataset downloaders."""
        downloaders = []
        
        hf_datasets = [
            ("ju-resplande/portuguese-fact-checking", "COVID19.BR (raw)", "COVID19.BR_raw"),
            ("ju-resplande/portuguese-fact-checking", "Fake.br (raw)", "Fake.br_raw"),
            ("ju-resplande/portuguese-fact-checking", "MuMiN-PT (raw)", "MuMiN-PT_raw"),
        ]
        for ds, subset, name in hf_datasets:
            downloaders.append(HuggingFaceDownloader(ds, subset, name))

        downloaders.append(
            URLDownloader(
                "https://raw.githubusercontent.com/cabrau/FakeWhatsApp.Br/master/data/2018/fakeWhatsApp.BR_2018.csv",
                "FakeWhatsApp.BR_2018.csv",
            )
        )
        downloaders.append(
            URLDownloader(
                "https://raw.githubusercontent.com/GoloMarcos/LLM4BrazilianFakeNews/main/300-noticias-v2-filtradas.csv",
                "LLM4BR_300.csv",
            )
        )

        try:
            downloaders.append(
                KaggleDownloader(
                    "fabioselau/fakes-news-portuguese",
                    ["fake.csv", "true.csv"],
                )
            )
        except Exception as e:
            logging.warning(f"Kaggle dataset skipped: {e}")

        return downloaders
    
    def download(self) -> List[str]:
        """
        Download all configured datasets.
        
        Returns:
            List of paths to downloaded files.
        """
        all_paths = []
        for downloader in self.downloaders:
            try:
                paths = downloader.download(self.raw_dir)
                all_paths.extend(paths)
                print(f"Downloaded {len(paths)} file(s) from {downloader.__class__.__name__}")
            except Exception as e:
                print(f"Failed to download from {downloader.__class__.__name__}: {e}")
        return all_paths
    
    def normalize_and_merge(
        self, local_files: Optional[Dict[str, Dict[str, str]]] = None
    ) -> pd.DataFrame:
        """Normalize schemas and merge all datasets."""
        frames = []
        dataset_stats = {}

        for fn in os.listdir(self.raw_dir):
            if fn.startswith(".") or fn == "manifest.json":
                continue

            path = os.path.join(self.raw_dir, fn)
            if not os.path.isfile(path):
                continue

            try:
                if fn.endswith(".parquet"):
                    df = pd.read_parquet(path)
                elif fn.endswith(".csv"):
                    df = pd.read_csv(path, low_memory=False)
                else:
                    continue

                dataset_name = fn.replace(".parquet", "").replace(".csv", "")
                df_norm = ensure_schema(
                    df,
                    dataset_name=dataset_name,
                    source_type="news",
                    source_description=f"Dataset {dataset_name}",
                )
                frames.append(df_norm)
                dataset_stats[dataset_name] = len(df_norm)
                print(f"Normalized {dataset_name}: {len(df_norm)} records")

            except Exception as e:
                print(f"Failed to process {fn}: {e}")

        # Handle FakeTweetBr tweet_id extraction
        for i, _df in enumerate(frames):
            if "dataset_name" in _df.columns and _df["dataset_name"].eq("FakeTweetBr").any():
                mask = _df["dataset_name"].eq("FakeTweetBr")
                _df.loc[mask, "tweet_id"] = _df.loc[mask, "url_claim"].apply(extract_tweet_id)
                _df.loc[mask, "orig_id"] = _df.loc[mask, "tweet_id"]
                frames[i] = _df

        frames = assign_uids(frames)
        df_final = pd.concat(frames, ignore_index=True)

        df_final = df_final[df_final["text"].notna()]
        df_final = df_final.drop_duplicates(subset=["text"])
        df_final = df_final.drop(columns=["language", "uid"], errors="ignore")

        cols_order = [
            "dataset_name",
            "source_type",
            "source_description",
            "label",
            "date_iso",
            "orig_id",
            "tweet_id",
            "url_claim",
            "url_review",
            "text",
        ]
        df_final = df_final.reindex(
            columns=[c for c in cols_order if c in df_final.columns]
            + [c for c in df_final.columns if c not in cols_order]
        )

        print("\n=== Merge Statistics ===")
        print(f"Total rows: {len(df_final)}")
        print(f"By dataset:\n{df_final['dataset_name'].value_counts()}")
        print(f"By label:\n{df_final['label'].value_counts(dropna=False)}")

        return df_final
    
    def save_merged(self, df: pd.DataFrame) -> tuple[str, str]:
        """Save merged dataset to CSV and Parquet."""
        csv_path = os.path.join(self.out_dir, "FakenewsBR_merged.csv")
        parquet_path = os.path.join(self.out_dir, "FakenewsBR_merged.parquet")

        df.to_csv(csv_path, index=False)

        text_like = [
            "label",
            "text",
            "orig_id",
            "url_claim",
            "url_review",
            "dataset_name",
            "source_type",
            "source_description",
            "date_iso",
            "tweet_id",
        ]
        for c in text_like:
            if c in df.columns:
                try:
                    df[c] = df[c].astype("string[pyarrow]")
                except TypeError:
                    df[c] = df[c].astype("string")

        df.to_parquet(parquet_path, index=False)
        save_manifest(self.out_dir)

        print(f"Saved merged dataset to:\n  {csv_path}\n  {parquet_path}")
        return csv_path, parquet_path
    
    def clean(self, input_path: Optional[str] = None) -> pd.DataFrame:
        """Clean dataset using DatasetCleaner."""
        if input_path is None:
            input_path = os.path.join(self.out_dir, "FakenewsBR_merged.csv")

        cleaner = DatasetCleaner(min_tokens=self.config.get("min_tokens", 5))
        df_clean = cleaner.clean_dataset(
            input_path,
            save_csv=os.path.join(self.out_dir, "FakenewsBR_clean.csv"),
            save_parquet=os.path.join(self.out_dir, "FakenewsBR_clean.parquet"),
        )
        return df_clean
    
    def add_deduplication(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add near-duplicate detection."""
        dup_config = self.config.get("deduplication", {})
        detector = DuplicateDetector(
            threshold=dup_config.get("threshold", 0.7),
            ngram=dup_config.get("ngram", 5),
            seed=dup_config.get("seed", 3),
            num_perm=dup_config.get("num_perm", 128),
            bands=dup_config.get("bands", 50),
        )

        texts = df["text_clean"].fillna("").tolist()
        near_dups = detector.find_near_duplicates(texts)
        df["near_duplicates"] = df.index.map(lambda i: near_dups.get(i, []))
        return df
    
    def factcheck(self, input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
        """Run Google Fact Check on dataset."""
        api_key = self.config.get("factcheck_api_key")
        if not api_key:
            raise ValueError("factcheck_api_key not set in configuration")

        if input_path is None:
            input_path = os.path.join(self.out_dir, "FakenewsBR_clean.csv")

        if output_path is None:
            output_path = os.path.join(self.out_dir, "FakenewsBR_factchecked.csv")

        checker = FactChecker(
            api_key=api_key,
            max_workers=self.config.get("max_workers", 31),
            max_inflight=self.config.get("max_inflight", 200),
            sleep_time=self.config.get("factcheck_sleep", 1.0),
        )

        return checker.process_dataset(input_path, output_path, self.out_dir)
    
    def run_full_pipeline(self, skip_download: bool = False) -> Dict[str, str]:
        """Run complete pipeline from download to fact-checking."""
        results = {}

        if not skip_download:
            print("\n=== Step 1: Downloading datasets ===")
            self.download()

        print("\n=== Step 2: Normalizing and merging ===")
        df_merged = self.normalize_and_merge()
        csv_path, parquet_path = self.save_merged(df_merged)
        results["merged_csv"] = csv_path
        results["merged_parquet"] = parquet_path

        print("\n=== Step 3: Cleaning dataset ===")
        self.clean()
        results["clean_csv"] = os.path.join(self.out_dir, "FakenewsBR_clean.csv")
        results["clean_parquet"] = os.path.join(self.out_dir, "FakenewsBR_clean.parquet")

        if self.config.get("factcheck_api_key"):
            print("\n=== Step 4: Running Fact Check ===")
            factcheck_path = self.factcheck()
            results["factchecked_csv"] = factcheck_path
        else:
            print("\n=== Step 4: Skipping Fact Check (no API key) ===")

        print("\n=== Pipeline Complete ===")
        print("Output files:")
        for key, path in results.items():
            print(f"  {key}: {path}")

        return results

if __name__ == "__main__":
    print("Starting full pipeline...\n")

    pipeline = Pipeline(config_path="config.json")
    results = pipeline.run_full_pipeline(skip_download=False)

    print("\nPipeline execution completed successfully!")
    print("Results summary::")
    for key, value in results.items():
        print(f"{key}: {value}")



