"""Main pipeline orchestration for dataset processing."""

import os
import json
from typing import List, Optional, Dict, Any
import pandas as pd
from loguru import logger

from fakenews_br_data.config import load_config
from fakenews_br_data.downloaders import (
    HuggingFaceDownloader,
    URLDownloader,
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

        log_level = self.config.get("log_level", "INFO").upper()
        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level=log_level)

        self.out_dir = self.config.get("out_dir", "data")
        self.raw_dir = os.path.join(self.out_dir, "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

        self.downloaders = self._setup_downloaders()

        # Mapeamento de source_type por dataset
        self.source_type_map: Dict[str, str] = {
            "COVID19.BR": "news",
            "Fake.br": "tweets",
            "MuMiN-PT": "news",
            "FakeWhatsApp.BR_2018": "whatsapp messages",
            "LLM4BR_300": "brazilian news about politics",
            "fake": "tweets with only fake news",
            "true": "tweets with only true info",
        }
    
    def _setup_downloaders(self) -> List:
        """Setup dataset downloaders."""
        downloaders = []
        
        hf_datasets = [
            ("ju-resplande/portuguese-fact-checking", "COVID19.BR", "COVID19.BR"),
            ("ju-resplande/portuguese-fact-checking", "Fake.br", "Fake.br"),
            ("ju-resplande/portuguese-fact-checking", "MuMiN-PT", "MuMiN-PT"),
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
            logger.warning(f"Kaggle dataset skipped: {e}")

        return downloaders
    
    def download(self) -> List[str]:
        """
        Download all configured datasets.
        
        Returns:
            List of paths to downloaded files.
        """
        logger.info("[Pipeline] Step 1: Downloading datasets")
        all_paths = []
        show_progress = self.config.get("show_progress_bar", True)
        for downloader in self.downloaders:
            try:
                paths = downloader.download(self.raw_dir, show_progress_bar=show_progress)
                all_paths.extend(paths)
                logger.info(f"[Pipeline] {downloader.__class__.__name__}: {len(paths)} file(s) downloaded")
            except Exception as e:
                logger.error(f"[Pipeline] Failed to download from {downloader.__class__.__name__}: {e}")
        return all_paths
    
    
    def _iter_raw_files(self) -> List[str]:
        """Recursively list all CSV/Parquet files under self.raw_dir."""
        files = []
        for root, _, fns in os.walk(self.raw_dir):
            for fn in fns:
                if fn.startswith(".") or fn == "manifest.json":
                    continue
                if fn.lower().endswith((".csv", ".parquet")):
                    files.append(os.path.join(root, fn))
        return files

    def normalize_and_merge(
        self, local_files: Optional[Dict[str, Dict[str, str]]] = None
    ) -> tuple[pd.DataFrame, Dict[str, int]]:
        """Normalize schemas and merge all datasets."""
        logger.info("[Pipeline] Step 2: Normalizing and merging")

        frames: List[pd.DataFrame] = []
        dataset_counts: Dict[str, int] = {}
        total_files = 0

        for path in self._iter_raw_files():
            total_files += 1
            fn = os.path.basename(path)

            try:
                if path.lower().endswith(".parquet"):
                    df = pd.read_parquet(path)
                elif path.lower().endswith(".csv"):
                    df = pd.read_csv(path, low_memory=False)
                else:
                    continue

                dataset_name = os.path.splitext(fn)[0]
                source_type = self.source_type_map.get(dataset_name, "news")
                df_norm = ensure_schema(
                    df,
                    dataset_name=dataset_name,
                    source_type=source_type,
                    source_description=f"Dataset {dataset_name}",
                    #log_level=self.config.get("log_level", "INFO"),
                )
                if "url_review" in df_norm.columns and df_norm["url_review"].isna().all():
                    logger.info(f"[Pipeline] {dataset_name}: url_review totalmente ausente após normalização")

                if df_norm is None or df_norm.empty:
                    logger.warning(f"[Pipeline] Skipping empty dataset after normalization: {dataset_name}")
                    continue

                frames.append(df_norm)
                dataset_counts[dataset_name] = len(df_norm)
                logger.info(f"[Pipeline] Normalized {dataset_name}: {len(df_norm)} records")

            except Exception as e:
                logger.error(f"[Pipeline] Failed to process {fn}: {e}")

        for i, _df in enumerate(frames):
            if "dataset_name" in _df.columns and _df["dataset_name"].eq("FakeTweetBr").any():
                mask = _df["dataset_name"].eq("FakeTweetBr")
                _df.loc[mask, "tweet_id"] = _df.loc[mask, "url_claim"].apply(extract_tweet_id)
                frames[i] = _df

        frames = assign_uids(frames)
        if not frames:
            logger.warning("[Pipeline] No datasets available after normalization")
            return pd.DataFrame(), {}

        df_final = pd.concat(frames, ignore_index=True)

        if "text" in df_final.columns:
            before = len(df_final)
            df_final = df_final[df_final["text"].notna()]
            logger.info(f"[Pipeline] Removed rows with null text: {before - len(df_final)}")

        cols_order = [
            "dataset_name",
            "source_type",
            "source_description",
            "label",
            "date_iso",
            "tweet_id",
            "url_claim",
            "url_review",
            "text",
        ]
        df_final = df_final.reindex(
            columns=[c for c in cols_order if c in df_final.columns]
            + [c for c in df_final.columns if c not in cols_order]
        )

        logger.info("\n[Pipeline] === Merge Statistics ===")
        logger.info(f"[Pipeline] Files scanned: {total_files}")
        logger.info(f"[Pipeline] Total rows (normalized, concatenated): {len(df_final)}")

        if "dataset_name" in df_final.columns:
            vc = df_final["dataset_name"].value_counts(dropna=False)
            logger.info(f"[Pipeline] By dataset:\n{vc.to_string()}")
        if "label" in df_final.columns:
            vl = df_final["label"].value_counts(dropna=False)
            logger.info(f"[Pipeline] By label:\n{vl.to_string()}")

        return df_final, dataset_counts
    
    def _save_dataset_stats(self, normalized_counts: Dict[str, int], merged_total: int) -> None:
        """Save dataset statistics to dataset_stats.json."""
        stats_path = os.path.join(self.out_dir, "dataset_stats.json")
        data = {
            "normalized_counts": normalized_counts,
            "merged_total_rows": merged_total,
        }
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"[Pipeline] Saved dataset stats at: {stats_path}")
    
    def save_merged(self, df: pd.DataFrame) -> tuple[str, str]:
        """Save merged dataset to CSV and Parquet."""
        csv_path = os.path.join(self.out_dir, "FakenewsBR_merged.csv")
        parquet_path = os.path.join(self.out_dir, "FakenewsBR_merged.parquet")

        df.to_csv(csv_path, index=False)

        text_like = [
            "label",
            "text",
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

        logger.info(f"[Pipeline] Saved merged dataset:\n  {csv_path}\n  {parquet_path}")
        return csv_path, parquet_path
    
    def clean(self, input_path: Optional[str] = None) -> pd.DataFrame:
        """Clean dataset using DatasetCleaner."""
        if input_path is None:
            input_path = os.path.join(self.out_dir, "FakenewsBR_merged.csv")

        cleaner = DatasetCleaner(min_tokens=self.config.get("min_tokens", 3))
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
            threshold=dup_config.get("threshold", 0.85),
            ngram=dup_config.get("ngram", 3),
            seed=dup_config.get("seed", 3),
            num_perm=dup_config.get("num_perm", 64),
            bands=dup_config.get("bands", 50),
        )

        if "text_clean" not in df.columns:
            logger.warning("[Pipeline] text_clean not found. Skipping near-duplicate detection.")
            return df

        logger.info("[Pipeline] Running near-duplicate detection...")
        texts = df["text_clean"].fillna("").tolist()
        show_progress = self.config.get("show_progress_bar", True)
        near_dups = detector.find_near_duplicates(texts, show_progress_bar=show_progress)
        df = df.copy()
        df["near_duplicates"] = df.index.map(lambda i: near_dups.get(i, []))
        logger.info("[Pipeline] Near-duplicate detection finished")
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
            max_query_size=self.config.get("max_query_size", 512),
            language_code=self.config.get("language_code", "pt-BR"),
            show_progress_bar=self.config.get("show_progress_bar", True),
        )

        return checker.process_dataset(input_path, output_path, self.out_dir)
    
    def run_full_pipeline(self, skip_download: bool = False) -> Dict[str, str]:
        """Run complete pipeline from download to fact-checking."""
        results = {}

        if not skip_download:
            logger.info("\n=== Step 1: Downloading datasets ===")
            self.download()

        logger.info("\n=== Step 2: Normalizing and merging ===")
        df_merged, normalized_counts = self.normalize_and_merge()
        if df_merged is None or df_merged.empty:
            logger.error("[Pipeline] No data available after normalization and merge. Aborting.")
            return {}
        
        csv_path, parquet_path = self.save_merged(df_merged)
        results["merged_csv"] = csv_path
        results["merged_parquet"] = parquet_path
        self._save_dataset_stats(normalized_counts, merged_total=len(df_merged))
        logger.info("\n[Preview] Step 2 · normalized+merged")
        logger.info(f"\n{df_merged.head(5)}")

        logger.info("\n=== Step 3: Cleaning dataset ===")
        df_clean = self.clean()
        results["clean_csv"] = os.path.join(self.out_dir, "FakenewsBR_clean.csv")
        results["clean_parquet"] = os.path.join(self.out_dir, "FakenewsBR_clean.parquet")
        logger.info("\n[Preview] Step 3 · cleaned")
        logger.info(f"\n{df_clean.head(5)}")

        if self.config.get("enable_deduplication", False):
            logger.info("\n=== Optional: Near-duplicate detection ===")
            cleaned_df = pd.read_parquet(results["clean_parquet"])
            cleaned_df = self.add_deduplication(cleaned_df)
            cleaned_df.to_parquet(results["clean_parquet"], index=False)
            logger.info("[Pipeline] Updated cleaned Parquet with near_duplicates column")
            logger.info("\n[Preview] Step 3b · cleaned+near_duplicates")
            logger.info(f"\n{cleaned_df.head(5)}")

        if self.config.get("factcheck_api_key"):
            logger.info("\n=== Step 4: Running Fact Check ===")
            factcheck_path = self.factcheck()
            results["factchecked_csv"] = factcheck_path
            try:
                df_fc = pd.read_csv(factcheck_path, low_memory=False)
            except Exception:
                try:
                    df_fc = pd.read_parquet(factcheck_path)
                except Exception:
                    df_fc = None
            if df_fc is not None:
                logger.info("\n[Preview] Step 4 · factchecked")
                logger.info(f"\n{df_fc.head(5)}")
            else:
                logger.info("\n=== Step 4: Skipping Fact Check (no API key) ===")

        logger.info("\n=== Pipeline Complete ===")
        logger.info("Output files:")
        for key, path in results.items():
            logger.info(f"  {key}: {path}")

        return results

if __name__ == "__main__":
    logger.info("Starting full pipeline...\n")

    pipeline = Pipeline(config_path="config.toml")
    results = pipeline.run_full_pipeline(skip_download=True)

    logger.info("\nPipeline execution completed successfully!")
    logger.info("Results summary::")
    for key, value in results.items():
        logger.info(f"{key}: {value}")

