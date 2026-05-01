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

DATASET_DESCRIPTIONS = {
    "MuMiN-PT": "Portuguese subset of MuMiN with verified claims and associated tweets.",
    "COVID19.BR": "Brazilian Portuguese WhatsApp messages about COVID-19 collected from public groups in 2020.",
    "Fake.br": "Brazilian news dataset with aligned pairs of false and true texts on the same topics.",
    "FakeTweetBr": "Brazilian Portuguese tweets labeled for veracity, used for studying rumors and fake news.",
    "FakeWhatsApp.BR_2018": "Public Brazilian Portuguese WhatsApp messages from 2018 annotated for misinformation detection.",
    "LLM4BR_300": "A set of 300 Brazilian political news articles used to evaluate LLMs in textual misinformation detection.",
    "fake": "Fake news from the Kaggle dataset fabioselau/fakes-news-portuguese.",
    "true": "True news from the Kaggle dataset fabioselau/fakes-news-portuguese.",
}


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

        # Mapping of source_type by dataset
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

    def _clean_url_claim(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """
        Cleans the url_claim column:
        - Converts obviously invalid values (0, 1, pure numeric values, etc.) into NA.
        - Keeps only strings that look like valid URLs.
        """
        if df is None or df.empty or "url_claim" not in df.columns:
            return df

        import re
        from urllib.parse import urlparse

        def is_probably_url(value: str) -> bool:
            s = value.strip()
            if not s:
                return False

            # Values that we know are junk
            if s in {"0", "1"}:
                return False

            # Pure numeric: 123, 50.000, 3.14, etc.
            if re.fullmatch(r"[0-9]+([.,][0-9]+)?", s):
                return False

            # Try to interpret as URL (add scheme if missing)
            candidate = s
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate):
                candidate = "http://" + candidate

            parsed = urlparse(candidate)

            # Simple rule: must have a host with at least one dot.
            if not parsed.netloc or "." not in parsed.netloc:
                return False

            return True

        before = df["url_claim"].notna().sum()

        def normalize(v):
            if pd.isna(v):
                return pd.NA
            s = str(v).strip()
            if not is_probably_url(s):
                return pd.NA
            return s

        df = df.copy()
        df["url_claim"] = df["url_claim"].map(normalize)

        after = df["url_claim"].notna().sum()
        logger.info(
            f"[Pipeline] {dataset_name}: cleaning url_claim "
            f"({before} non-null values -> {after} plausible URLs)"
        )
        return df


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
                description = DATASET_DESCRIPTIONS.get(
                    dataset_name,
                    f"Dataset {dataset_name}",  
                )

                df_norm = ensure_schema(
                    df,
                    dataset_name=dataset_name,
                    source_type=source_type,
                    source_description=description,
                )

                # Clean url_claim (remove 0, 1, numeric values, and obvious non-URLs)
                df_norm = self._clean_url_claim(df_norm, dataset_name)

                if "url_review" in df_norm.columns and df_norm["url_review"].isna().all():
                    logger.info(f"[Pipeline] {dataset_name}: url_review completely missing after normalization")

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
    
    def _unify_url_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Unifies URL columns and removes auxiliary columns in the final dataset:
        - Ensures url_review exists.
        - Fills url_review with values from url_claim where url_review is empty.
        - ALWAYS removes the url_claim column at the end, if it exists.
        - ALWAYS removes the uid column, if it exists.
        """
        if df is None or df.empty:
            return df

        df = df.copy()

        # --- Unification url_claim -> url_review (if url_claim exists) ---

        if "url_claim" in df.columns:
            # Ensure url_review exists
            if "url_review" not in df.columns:
                logger.info("[Pipeline] Creating url_review column (it did not exist).")
                df["url_review"] = pd.NA

            # Fill url_review with url_claim where url_review is empty
            mask = df["url_review"].isna() & df["url_claim"].notna()
            if mask.any():
                logger.info(f"[Pipeline] Filling url_review with {mask.sum()} values from url_claim.")
                df.loc[mask, "url_review"] = df.loc[mask, "url_claim"]

            # ALWAYS remove url_claim after unification
            logger.info("[Pipeline] Removing url_claim column after unification.")
            df = df.drop(columns=["url_claim"])

        # --- Removal of uid in the final dataset ---
        if "uid" in df.columns:
            logger.info("[Pipeline] Removing uid column from final dataset.")
            df = df.drop(columns=["uid"])

        return df

        """
        Unifies URL columns and removes url_claim:
        - Ensures url_review exists.
        - Fills url_review with values from url_claim where url_review is empty.
        - ALWAYS removes the url_claim column at the end.
        """
        if df is None or df.empty:
            return df

        df = df.copy()

        # If there is no url_claim, nothing to do
        if "url_claim" not in df.columns:
            return df

        # Ensure url_review exists
        if "url_review" not in df.columns:
            logger.info("[Pipeline] Creating url_review column (it did not exist).")
            df["url_review"] = pd.NA

        # Fill url_review with url_claim where url_review is empty
        mask = df["url_review"].isna() & df["url_claim"].notna()
        if mask.any():
            logger.info(f"[Pipeline] Filling url_review with {mask.sum()} values from url_claim.")
            df.loc[mask, "url_review"] = df.loc[mask, "url_claim"]

        # ALWAYS remove url_claim after unification
        logger.info("[Pipeline] Removing url_claim column after unification.")
        df = df.drop(columns=["url_claim"])

        return df
        """
        Unifies URL columns:
        - Fills url_review with values from url_claim when url_review is empty.
        - Creates url_review from url_claim if url_review does not exist.
        - Removes url_claim if, after unification, only empty/NA values remain.
        """
        if df is None or df.empty:
            return df

        df = df.copy()

        # If there is no url_claim, nothing to do
        if "url_claim" not in df.columns:
            return df

        # If there is no url_review, create it from url_claim (if there is something useful)
        if "url_review" not in df.columns:
            if df["url_claim"].notna().any():
                logger.info("[Pipeline] Creating url_review column from url_claim (url_review not present).")
                df["url_review"] = df["url_claim"]
            else:
                # url_claim exists but only contains empty values → remove it
                non_empty_claim = df["url_claim"].notna() & (df["url_claim"].astype(str).str.strip() != "")
                if not non_empty_claim.any():
                    logger.info("[Pipeline] Removing url_claim column (only empty values).")
                    df = df.drop(columns=["url_claim"])
                return df
        # 1) Fill url_review with url_claim when empty
        mask = df["url_review"].isna() & df["url_claim"].notna()
        if mask.any():
            logger.info(f"[Pipeline] Filling url_review with {mask.sum()} values from url_claim.")
            df.loc[mask, "url_review"] = df.loc[mask, "url_claim"]

        # 2) Check if anything remains in url_claim; if not, drop the column
        non_empty_claim = df["url_claim"].notna() & (df["url_claim"].astype(str).str.strip() != "")
        if not non_empty_claim.any():
            logger.info("[Pipeline] Removing url_claim column (only empty values after unification).")
            df = df.drop(columns=["url_claim"])

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
            max_workers=self.config.get("max_workers", 5),
            max_inflight=self.config.get("max_inflight", 200),
            sleep_time=self.config.get("factcheck_sleep", 1.0),
            max_query_size=self.config.get("max_query_size", 512),
            language_code=self.config.get("language_code", "pt-BR"),
            show_progress_bar=self.config.get("show_progress_bar", True),
        )

        return checker.process_dataset(input_path, output_path, self.out_dir)
    
    def run_full_pipeline(self, skip_download: bool = True) -> Dict[str, str]:
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

            # Read the fact-check result (CSV or Parquet)
            try:
                df_fc = pd.read_csv(factcheck_path, low_memory=False)
            except Exception:
                try:
                    df_fc = pd.read_parquet(factcheck_path)
                except Exception:
                    df_fc = None

            if df_fc is not None:
                # Unify url_claim/url_review and remove url_claim if it becomes empty
                df_fc = self._unify_url_columns(df_fc)

                # Save back to the same path
                if factcheck_path.lower().endswith(".csv"):
                    df_fc.to_csv(factcheck_path, index=False)
                else:
                    df_fc.to_parquet(factcheck_path, index=False)

                logger.info("\n[Preview] Step 4 · factchecked (URLs unificadas)")
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

