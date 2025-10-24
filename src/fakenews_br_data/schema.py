"""Schema normalization functions for different dataset formats."""

import re
from typing import Optional, List
import pandas as pd


def extract_url(text: str) -> Optional[str]:
    """
    Extract first URL from text.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        First URL found, or None
    """
    m = re.search(r"https?://\S+", str(text) if text is not None else "")
    return m.group(0) if m else None


def extract_tweet_id(url: str) -> Optional[str]:
    """
    Extract tweet ID from Twitter/X URL.
    
    Args:
        url: Twitter/X URL
        
    Returns:
        Tweet ID or None
    """
    if not isinstance(url, str):
        return None
    m = re.search(r'twitter\.com/.*/status/(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'(\d{8,})', url)
    return m.group(1) if m else None


def normalize_date(series: pd.Series) -> pd.Series:
    """
    Normalize dates to ISO format (YYYY-MM-DD).
    
    Args:
        series: Pandas series with dates in various formats
        
    Returns:
        Series with normalized dates
    """
    fmts = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    
    def parse_one(x):
        if pd.isna(x):
            return pd.NaT
        s = str(x).strip()
        for fmt in fmts:
            try:
                return pd.to_datetime(s, format=fmt, errors="raise")
            except:
                pass
        return pd.to_datetime(s, errors="coerce")
    
    dt = series.apply(parse_one)
    return pd.to_datetime(dt, errors="coerce")


def pick_first(df: pd.DataFrame, cols: List[str], default=None):
    """
    Return first existing column from list.
    
    Args:
        df: DataFrame to search
        cols: List of column names to try
        default: Default value if none found
        
    Returns:
        Series or default value
    """
    for c in cols:
        if c in df.columns:
            return df[c]
    return default


def ensure_schema(
    df: pd.DataFrame,
    dataset_name: str,
    source_type: str,
    source_description: str,
) -> pd.DataFrame:
    """
    Normalize DataFrame to standard schema.
    
    Args:
        df: Input DataFrame with varying schema
        dataset_name: Name of the dataset
        source_type: Type of source (news, whatsapp, x, etc.)
        source_description: Description of the source
        
    Returns:
        DataFrame with normalized schema
    """
    id_cols = ["uid", "id", "ID", "post_id", "doc_id", "tweet_id"]
    date_cols = ["date", "data", "created_at", "publish_date", "time", "timestamp"]
    text_cols = [
        "text",
        "content",
        "full_text",
        "title_text",
        "claim",
        "body",
        "article_text",
        "message",
    ]
    label_cols = [
        "label",
        "verdict",
        "target",
        "misinformation",
        "classificacao",
        "Rótulo",
        "rotulo",
    ]
    url_claim_cols = ["url", "link", "permalink", "source", "source_url", "url_claim"]
    url_review_cols = ["review_url", "url_review", "factcheck_url", "url_factcheck"]

    orig_id = pick_first(df, id_cols)

    text = pick_first(df, text_cols)
    if text is None:
        title = pick_first(df, ["title", "headline"])
        body = pick_first(df, ["text", "content", "body", "article_text"])
        text = (
            (title.fillna("") + ". " + body.fillna(""))
            if (title is not None and body is not None)
            else (title if title is not None else body)
        )

    url_claim = pick_first(df, url_claim_cols)
    if url_claim is None:
        url_claim = df.apply(lambda r: extract_url(r.get("text", "")), axis=1)
    url_claim = url_claim.astype(str)

    url_review = pick_first(df, url_review_cols)
    if url_review is None:
        url_review = pd.Series([None] * len(df))

    label = pick_first(df, label_cols)
    if label is None:
        label = pd.Series([None] * len(df))
    label = (
        label.astype(str)
        .str.strip()
        .str.lower()
        .replace(
            {
                "1": "fake",
                "0": "true",
                "false": "false",
                "true": "true",
                "fake": "fake",
                "falso": "fake",
                "verdadeiro": "true",
                "real": "true",
                "misleading": "fake",
                "partly false": "mixed",
                "partly_true": "mixed",
                "mixed": "mixed",
            }
        )
    )

    date_raw = pick_first(df, date_cols)
    if date_raw is None:
        date_iso = pd.Series([pd.NaT] * len(df))
    else:
        date_iso = normalize_date(date_raw)
    date_iso = pd.to_datetime(date_iso, errors="coerce")
    date_iso = date_iso.dt.strftime("%Y-%m-%d")

    out = pd.DataFrame(
        {
            "orig_id": orig_id.astype(str) if orig_id is not None else None,
            "text": text,
            "label": label,
            "url_claim": url_claim,
            "url_review": url_review,
            "date_iso": date_iso,
        }
    )
    out["dataset_name"] = dataset_name
    out["source_type"] = source_type
    out["source_description"] = source_description
    return out


def assign_uids(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Assign sequential unique IDs across multiple DataFrames.
    
    Args:
        dfs: List of DataFrames
        
    Returns:
        List of DataFrames with uid column
    """
    next_uid = 1
    out = []
    for df in dfs:
        df = df.copy()
        df["uid"] = range(next_uid, next_uid + len(df))
        next_uid += len(df)
        out.append(df)
    return out

