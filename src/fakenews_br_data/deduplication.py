"""Near-duplicate detection using MinHash LSH."""

from typing import List, Dict
from datasketch import MinHash, MinHashLSH


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
    
    def find_near_duplicates(self, texts: List[str]) -> Dict[int, List[str]]:
        """
        Find near-duplicate texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary mapping index to list of similar indices
        """
        minhashes = []
        for t in texts:
            mh = MinHash(num_perm=self.num_perm, seed=self.seed)
            tokens = {t[i : i + self.ngram] for i in range(max(1, len(t) - self.ngram + 1))}
            for shingle in tokens:
                mh.update(shingle.encode("utf8"))
            minhashes.append(mh)

        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        for i, mh in enumerate(minhashes):
            lsh.insert(str(i), mh)

        near_dups = {}
        for i, mh in enumerate(minhashes):
            near_dups[i] = lsh.query(mh)
        return near_dups

