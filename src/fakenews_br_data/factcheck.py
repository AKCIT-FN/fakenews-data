"""Google Fact Check API integration."""

import csv
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from typing import Dict, Optional
import pandas as pd
import requests
from tqdm.auto import tqdm
from loguru import logger


_thread = threading.local()


def _get_session():
    """Get thread-local requests session."""
    if getattr(_thread, "s", None) is None:
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(
            pool_connections=4, pool_maxsize=4, max_retries=3
        )
        s.mount("https://", a)
        _thread.s = s
    return _thread.s


BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


class FactChecker:
    """
    Check claims using Google Fact Check API.
    """
    
    def __init__(
        self,
        api_key: str,
        max_workers: int = 31,
        max_inflight: int = 200,
        sleep_time: float = 1.0,
        max_query_size: int = 512,
        language_code: str = "pt-BR",
        show_progress_bar: bool = True,
    ):
        """
        Initialize FactChecker.
        
        Args:
            api_key: Google Fact Check API key
            max_workers: Maximum number of concurrent threads
            max_inflight: Maximum number of in-flight requests
            sleep_time: Sleep time between requests (seconds)
            max_query_size: Maximum query size in characters
            language_code: Language code for API requests
            show_progress_bar: Whether to show progress bar
        """
        self.api_key = api_key
        self.max_workers = max_workers
        self.max_inflight = max_inflight
        self.sleep_time = sleep_time
        self.max_query_size = max_query_size
        self.language_code = language_code
        self.show_progress_bar = show_progress_bar
    
    def check_claim(self, text: str) -> Dict[str, Optional[str]]:
        """
        Check a single claim via Google Fact Check API.
        
        Args:
            text: Claim text to check
            
        Returns:
            Dict with factcheck_rating, factcheck_claimant, factcheck_url
        """
        if not isinstance(text, str) or not text.strip():
            return {
                "factcheck_rating": None,
                "factcheck_claimant": None,
                "factcheck_url": None,
            }
        
        try:
            r = _get_session().get(
                BASE_URL,
                params={
                    "query": text[:self.max_query_size],
                    "pageSize": 1,
                    "languageCode": self.language_code,
                    "key": self.api_key,
                },
                timeout=12,
            )
            r.raise_for_status()
            resp = r.json()
            time.sleep(self.sleep_time)
            
            if resp.get("claims"):
                claim = resp["claims"][0]
                review = (claim.get("claimReview") or [{}])[0]
                return {
                    "factcheck_rating": review.get("textualRating", ""),
                    "factcheck_claimant": claim.get("claimant", ""),
                    "factcheck_url": review.get("url", ""),
                }
        except Exception:
            pass
        
        return {
            "factcheck_rating": None,
            "factcheck_claimant": None,
            "factcheck_url": None,
        }
    
    def _process_row(self, row: Dict) -> Dict:
        """Process a single row."""
        res = self.check_claim(row["text"])
        res["rid"] = row["rid"]
        return res
    
    def _rows_iter(self, df: pd.DataFrame):
        """Iterate over DataFrame rows."""
        for rid, txt in zip(df["rid"].values, df["text"].values):
            yield {"rid": int(rid), "text": txt}
    
    def run_factcheck_streaming(
        self, input_csv: str, output_dir: str
    ) -> str:
        """
        Run fact checking with streaming output.
        
        Args:
            input_csv: Path to input CSV file
            output_dir: Directory to save temporary results
            
        Returns:
            Path to temporary results CSV
        """
        base = pd.read_csv(
            input_csv, usecols=["text"]
        ).reset_index().rename(columns={"index": "rid"})
        
        os.makedirs(output_dir, exist_ok=True)
        tmp_csv = os.path.join(output_dir, "factcheck_tmp.csv")
        
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "rid",
                    "factcheck_rating",
                    "factcheck_claimant",
                    "factcheck_url",
                ],
            )
            w.writeheader()
            
            it = self._rows_iter(base)
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                inflight = set()
                for _ in range(min(self.max_inflight, len(base))):
                    try:
                        inflight.add(ex.submit(self._process_row, next(it)))
                    except StopIteration:
                        break
                
                pbar = tqdm(total=len(base), desc="Fact checking", disable=not self.show_progress_bar)
                while inflight:
                    done, inflight = wait(inflight, return_when=FIRST_COMPLETED)
                    for fut in done:
                        w.writerow(fut.result())
                        pbar.update(1)
                        try:
                            inflight.add(ex.submit(self._process_row, next(it)))
                        except StopIteration:
                            pass
                pbar.close()
        
        return tmp_csv
    
    def join_with_sqlite(
        self, input_csv: str, tmp_csv: str, output_csv: str, output_dir: str
    ) -> None:
        """
        Join original data with fact check results using SQLite.
        
        Args:
            input_csv: Path to original input CSV
            tmp_csv: Path to temporary fact check results
            output_csv: Path to save final joined CSV
            output_dir: Directory for temporary database
        """
        db = os.path.join(output_dir, "factcheck.db")
        if os.path.exists(db):
            os.remove(db)
        con = sqlite3.connect(db)

        offset = 0
        for chunk in pd.read_csv(input_csv, chunksize=100_000):
            n = len(chunk)
            chunk.insert(0, "rid", range(offset, offset + n))
            offset += n
            chunk.to_sql("base", con, if_exists="append", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS idx_base_rid ON base(rid)")

        for chunk in pd.read_csv(
            tmp_csv, chunksize=100_000, dtype={"rid": int}
        ):
            chunk.to_sql("fc", con, if_exists="append", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS idx_fc_rid ON fc(rid)")

        q = """
          SELECT b.*, f.factcheck_rating, f.factcheck_claimant, f.factcheck_url
          FROM base AS b
          LEFT JOIN fc AS f ON b.rid = f.rid
          ORDER BY b.rid
        """
        first = True
        for chunk in pd.read_sql_query(q, con, chunksize=100_000):
            chunk.to_csv(
                output_csv, index=False, mode=("w" if first else "a"), header=first
            )
            first = False
        con.close()
    
    def process_dataset(
        self, input_csv: str, output_csv: str, output_dir: str = "out"
    ) -> str:
        """
        Complete fact check pipeline for a dataset.
        
        Args:
            input_csv: Path to input CSV
            output_csv: Path to save final CSV
            output_dir: Directory for temporary files
            
        Returns:
            Path to output CSV
        """
        logger.info("Running Google Fact Check (streaming + JOIN by rid)...")
        tmp_csv = self.run_factcheck_streaming(input_csv, output_dir)
        self.join_with_sqlite(input_csv, tmp_csv, output_csv, output_dir)
        logger.info(f"Fact Check saved to: {output_csv}")
        return output_csv

