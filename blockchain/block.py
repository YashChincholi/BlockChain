import hashlib
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BlockHeader:
    """
    Block header containing metadata and links.
    Hash is computed only from the header.
    """
    index: int
    timestamp: float
    previous_hash: str
    merkle_root: str
    nonce: int = 0
    difficulty: int = 0

    def to_string(self) -> str:
        """Convert header to string for hashing."""
        return f"{self.index}{self.timestamp}{self.previous_hash}{self.merkle_root}{self.nonce}{self.difficulty}"

    def calculate_hash(self) -> str:
        """Calculate hash from header only."""
        return hashlib.sha256(self.to_string().encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce,
            'difficulty': self.difficulty
        }


@dataclass
class BlockBody:
    """
    Block body containing transactions and metadata.
    """
    transactions: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'transactions': self.transactions,
            'metadata': self.metadata
        }


class Block:
    """
    Full block with separated header and body.
    """

    def __init__(self,
                 index: int,
                 transactions: List[Dict],
                 previous_hash: str = "0",
                 timestamp: Optional[float] = None,
                 merkle_root: str = "",
                 nonce: int = 0,
                 difficulty: int = 0,
                 metadata: Optional[Dict] = None):

        if not isinstance(index, int) or index < 0:
            raise ValueError("Block index must be a non-negative integer")
        if not isinstance(previous_hash, str):
            raise ValueError("Previous hash must be a string")

        self.header = BlockHeader(
            index=index,
            timestamp=timestamp or time.time(),
            previous_hash=previous_hash,
            merkle_root=merkle_root,
            nonce=nonce,
            difficulty=difficulty
        )

        self.body = BlockBody(
            transactions=transactions if transactions else [],
            metadata=metadata if metadata else {}
        )

        self.hash = self.header.calculate_hash()

    @property
    def index(self) -> int:
        return self.header.index

    @property
    def timestamp(self) -> float:
        return self.header.timestamp

    @property
    def previous_hash(self) -> str:
        return self.header.previous_hash

    @property
    def merkle_root(self) -> str:
        return self.header.merkle_root

    @property
    def nonce(self) -> int:
        return self.header.nonce

    @property
    def difficulty(self) -> int:
        return self.header.difficulty

    @property
    def transactions(self) -> List[Dict]:
        return self.body.transactions

    @property
    def metadata(self) -> Dict:
        return self.body.metadata

    def calculate_hash(self) -> str:
        """Calculate hash from header."""
        try:
            return self.header.calculate_hash()
        except Exception as e:
            logger.error(f"Error calculating hash for block {self.index}: {e}")
            raise

    def get_formatted_timestamp(self) -> str:
        """Get human-readable timestamp."""
        return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> Dict:
        """Convert block to dictionary."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'formatted_timestamp': self.get_formatted_timestamp(),
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'hash': self.hash,
            'transactions': self.transactions,
            'metadata': self.metadata,
            'header': self.header.to_dict(),
            'body': self.body.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        """Create block from dictionary."""
        return cls(
            index=data['index'],
            transactions=data.get('transactions', []),
            previous_hash=data.get('previous_hash', '0'),
            timestamp=data.get('timestamp'),
            merkle_root=data.get('merkle_root', ''),
            nonce=data.get('nonce', 0),
            difficulty=data.get('difficulty', 0),
            metadata=data.get('metadata', {})
        )

    @property
    def data(self) -> str:
        """Backwards compatibility: return first transaction or metadata."""
        if self.transactions:
            return str(self.transactions[0].get('data', ''))
        return str(self.metadata.get('data', 'No data'))

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash={self.hash[:8]}..., txs={len(self.transactions)})"
