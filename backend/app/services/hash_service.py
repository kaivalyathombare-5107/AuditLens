"""
File hashing service
Location: backend/app/services/hash_service.py
"""

import hashlib
import os
from typing import Optional


class HashService:
    """Service for computing and verifying file hashes"""
    
    @staticmethod
    def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> Optional[str]:
        """Compute hash of a file"""
        try:
            hash_func = hashlib.new(algorithm)
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            print(f"Error computing hash: {e}")
            return None
    
    @staticmethod
    def verify_hash(filepath: str, expected_hash: str) -> bool:
        """Verify file hash against expected hash"""
        computed = HashService.compute_file_hash(filepath)
        return computed == expected_hash if computed else False
