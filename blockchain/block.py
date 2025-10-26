import hashlib
import time
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index: int, data: str, timestamp: Optional[float] = None, previous_hash: str = "0"):
        if not isinstance(index, int) or index < 0:
            raise ValueError("Block index must be a non-negative integer")
        if not data or not isinstance(data, str):
            raise ValueError("Block data must be a non-empty string")
        if not isinstance(previous_hash, str):
            raise ValueError("Previous hash must be a string")

        self.index = index
        self.timestamp = timestamp or time.time()
        self.data = data.strip()
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        try:
            block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}"
            return hashlib.sha256(block_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for block {self.index}: {e}")
            raise

    def get_formatted_timestamp(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'formatted_timestamp': self.get_formatted_timestamp(),
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }
