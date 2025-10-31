"""Near-duplicate detection using MinHash LSH."""

from typing import List, Dict
from datasketch import MinHash, MinHashLSH
from tqdm.auto import tqdm


class DuplicateDetector:
    """
    Detect near-duplicate texts using MinHash and Locality-Sensitive Hashing.
    """
    
    def __init__(
        self,
        threshold: float = 0.7,
        ngram: int = 5,
        seed: int = 3,
        num_perm: int = 128,
        bands: int = 50,
    ):
        """
        Initialize DuplicateDetector.
        
        Args:
            threshold: Jaccard similarity threshold (0.0 to 1.0)
            ngram: N-gram size for shingling
            seed: Random seed for MinHash
            num_perm: Number of permutations for MinHash
            bands: Number of bands for LSH (unused, kept for compatibility)
        """
        self.threshold = threshold
        self.ngram = ngram
        self.seed = seed
        self.num_perm = num_perm
        self.bands = bands
    
    def find_near_duplicates(self, texts: List[str], show_progress_bar: bool = True) -> Dict[int, List[str]]:
        """
        Find near-duplicate texts.
        
        Args:
            texts: List of text strings
            show_progress_bar: Whether to show progress bar
            
        Returns:
            Dictionary mapping index to list of similar indices
        """
        minhashes = []
        pbar = tqdm(texts, desc="Building MinHashes", disable=not show_progress_bar)
        for t in pbar:
            mh = MinHash(num_perm=self.num_perm, seed=self.seed)
            tokens = {t[i : i + self.ngram] for i in range(max(1, len(t) - self.ngram + 1))}
            for shingle in tokens:
                mh.update(shingle.encode("utf8"))
            minhashes.append(mh)
        pbar.close()

        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        pbar = tqdm(enumerate(minhashes), total=len(minhashes), desc="Inserting into LSH", disable=not show_progress_bar)
        for i, mh in pbar:
            lsh.insert(str(i), mh)
        pbar.close()

        near_dups = {}
        pbar = tqdm(enumerate(minhashes), total=len(minhashes), desc="Querying duplicates", disable=not show_progress_bar)
        for i, mh in pbar:
            near_dups[i] = lsh.query(mh)
        pbar.close()
        return near_dups

