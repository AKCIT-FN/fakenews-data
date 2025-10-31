"""Text cleaning and preprocessing functions."""

import re
import unicodedata
import pandas as pd
import demoji
from typing import Tuple, List
from urlextract import URLExtract
from loguru import logger

extractor = URLExtract()


def remove_outer_quotes(text: str) -> str:
    """
    Remove outer quotes (single or double) from text.
    
    Args:
        text: Input text
        
    Returns:
        Text without outer quotes
    """
    if not isinstance(text, str):
        return text
    text = text.strip()
    return re.sub(r'^(["""\'\'\'])(.*)([""\'\'\'])$', r'\2', text)


def normalize_accents(text: str) -> str:
    """
    Remove accents from text.
    
    Args:
        text: Input text
        
    Returns:
        Text without accents
    """
    if not isinstance(text, str):
        return text
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def remove_emojis(text: str) -> str:
    """
    Remove emojis from text.
    
    Args:
        text: Input text
        
    Returns:
        Text without emojis
    """
    if not isinstance(text, str):
        return text
    return demoji.replace(text, "")


def remove_urls(text: str) -> Tuple[str, List[str]]:
    """
    Remove URLs from text and return both cleaned text and extracted URLs.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (cleaned text, list of URLs found)
    """
    if not isinstance(text, str):
        return text, []
    urls = extractor.find_urls(text)
    for url in urls:
        text = text.replace(url, "")
    return text.strip(), urls


def normalize_spaces(text: str) -> str:
    """
    Replace multiple spaces with single space.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized spaces
    """
    if not isinstance(text, str):
        return text
    return re.sub(r"\s+", " ", text).strip()


def clean_for_factcheck(text: str) -> str:
    """
    Clean text pipeline for Google Fact Check API.
    
    Applies: strip, remove emojis, remove outer quotes, normalize accents,
    lowercase, normalize spaces.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return text
    text = text.strip()
    text = remove_emojis(text)
    text = remove_outer_quotes(text)
    text = normalize_accents(text)
    text = text.lower()
    text = normalize_spaces(text)
    return text


class DatasetCleaner:
    """
    Clean and preprocess datasets with deduplication and quality filtering.
    """
    
    def __init__(self, min_tokens: int = 3):
        """
        Initialize DatasetCleaner.
        
        Args:
            min_tokens: Minimum number of tokens required
        """
        self.min_tokens = min_tokens
    
    def clean_dataset(
        self,
        path: str,
        save_csv: str = "data/FakenewsBR_clean.csv",
        save_parquet: str = "data/FakenewsBR_clean.parquet",
    ) -> pd.DataFrame:
        """
        Clean dataset with full pipeline.
        
        Args:
            path: Path to input dataset (CSV or Parquet)
            save_csv: Path to save cleaned CSV
            save_parquet: Path to save cleaned Parquet
            
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"[Cleaning] Loading dataset from {path}")

        if path.endswith(".parquet"):
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, low_memory=False)

        initial_rows = len(df)
        logger.info(f"[Cleaning] Loaded {initial_rows} rows")

        df["label"] = (
            df["label"]
            .astype(str)
            .str.strip()
            .str.lower()
            .replace({
                "-1": None,
                "none": None,
                "nan": None,
                "": None,
                "falso": "fake",
                "falsa": "fake",
                "fake": "fake",
                "false": "fake",
                "verdadeiro": "true",
                "verdadeira": "true",
                "true": "true",
                "real": "true",
            })
        )
        df = df[df["label"].isin(["fake", "true"])].copy()
        logger.info(f"[Cleaning] After label filtering: {len(df)} rows remain")

        df["text_no_url"], df["extracted_urls"] = zip(*df["text"].apply(remove_urls))
        df["text_clean"] = df["text_no_url"].apply(clean_for_factcheck)

        if "dataset_name" in df.columns:
            df["is_duplicated"] = (
                df.groupby("dataset_name")["text_clean"]
                .transform(lambda x: x.duplicated())
            )
        else:
            df["is_duplicated"] = df["text_clean"].duplicated()

        df["is_null"] = df["text_clean"].isna()
        df["too_short"] = df["text_clean"].apply(
            lambda t: len(t.split()) < self.min_tokens if pd.notna(t) else True
        )

        df_clean = df[~(df["is_null"] | df["is_duplicated"] | df["too_short"])].copy()
        df_clean.reset_index(drop=True, inplace=True)

        drop_candidates = ["language"]
        for c in drop_candidates:
            if c in df_clean.columns:
                df_clean.drop(columns=[c], inplace=True)

        cols_order_clean = [
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
            "text_clean",
        ]
        cols_order_clean = [c for c in cols_order_clean if c in df_clean.columns] + [
            c for c in df_clean.columns if c not in cols_order_clean
        ]
        df_clean = df_clean.reindex(columns=cols_order_clean)

        df_clean.to_csv(save_csv, index=False)

        text_like = [
            "label",
            "text",
            "text_clean",
            "orig_id",
            "url_claim",
            "url_review",
            "dataset_name",
            "source_type",
            "source_description",
            "date_iso",
            "factcheck_rating",
            "factcheck_claimant",
            "dataset_url",
            "tweet_id",
        ]
        for c in text_like:
            if c in df_clean.columns:
                try:
                    df_clean[c] = df_clean[c].astype("string[pyarrow]")
                except TypeError:
                    df_clean[c] = df_clean[c].astype("string")

        df_clean.to_parquet(save_parquet, index=False)

        logger.info(f"[Cleaning] Finished cleaning. {len(df_clean)} rows remain (from {initial_rows})")
        logger.info(f"[Cleaning] Label distribution:\n{df_clean['label'].value_counts(dropna=False)}")
        logger.info(f"[Cleaning] Saved cleaned files: {save_csv}, {save_parquet}")

        return df_clean

