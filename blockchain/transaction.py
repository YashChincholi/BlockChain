import time
import uuid
import logging
from typing import Optional, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """
    Represents a transaction in the blockchain.
    """
    sender: str
    recipient: str
    amount: float
    fee: float = 0.0
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signature: Optional[str] = None
    data: Optional[Dict] = None

    def __post_init__(self):
        """Validate transaction data after initialization."""
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        if self.fee < 0:
            raise ValueError("Transaction fee cannot be negative")
        if not self.sender or not self.recipient:
            raise ValueError("Sender and recipient are required")

    def to_dict(self) -> Dict:
        """Convert transaction to dictionary."""
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'fee': self.fee,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'data': self.data
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create a transaction from a dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            sender=data['sender'],
            recipient=data['recipient'],
            amount=data['amount'],
            fee=data.get('fee', 0.0),
            timestamp=data.get('timestamp', time.time()),
            signature=data.get('signature'),
            data=data.get('data')
        )

    def get_transaction_string(self) -> str:
        """Get a string representation for hashing/signing."""
        return f"{self.id}{self.sender}{self.recipient}{self.amount}{self.fee}{self.timestamp}"

    def sign(self, private_key) -> None:
        """
        Sign the transaction with a private key.
        This is a placeholder for now - actual implementation will use cryptography.
        """
        pass

    def verify_signature(self, public_key) -> bool:
        """
        Verify the transaction signature.
        This is a placeholder for now - actual implementation will use cryptography.
        """
        if not self.signature:
            return False
        return True

    def __repr__(self) -> str:
        return f"Transaction({self.id[:8]}...: {self.sender[:8]}... -> {self.recipient[:8]}... Amount: {self.amount})"


class CoinbaseTransaction(Transaction):
    """
    Special transaction type for block rewards.
    """

    def __init__(self, recipient: str, reward: float, fees: float = 0.0):
        super().__init__(
            sender="COINBASE",
            recipient=recipient,
            amount=reward + fees,
            fee=0.0
        )
        self.reward = reward
        self.fees_collected = fees

    def to_dict(self) -> Dict:
        """Convert coinbase transaction to dictionary."""
        data = super().to_dict()
        data['type'] = 'coinbase'
        data['reward'] = self.reward
        data['fees_collected'] = self.fees_collected
        return data


class TransactionPool:
    """
    Manages pending transactions (mempool).
    """

    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        logger.info("Transaction pool initialized")

    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a transaction to the pool."""
        try:
            if transaction.id in self.transactions:
                logger.warning(f"Transaction {transaction.id} already in pool")
                return False

            self.transactions[transaction.id] = transaction
            logger.info(f"Transaction {transaction.id[:8]}... added to pool")
            return True

        except Exception as e:
            logger.error(f"Error adding transaction to pool: {e}")
            return False

    def remove_transaction(self, transaction_id: str) -> bool:
        """Remove a transaction from the pool."""
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
            logger.info(f"Transaction {transaction_id[:8]}... removed from pool")
            return True
        return False

    def get_transactions(self, limit: Optional[int] = None) -> list:
        """Get transactions from the pool."""
        transactions = list(self.transactions.values())
        if limit:
            transactions = transactions[:limit]
        return transactions

    def clear(self):
        """Clear all transactions from the pool."""
        count = len(self.transactions)
        self.transactions.clear()
        logger.info(f"Transaction pool cleared ({count} transactions removed)")

    def get_total_fees(self, transactions: list = None) -> float:
        """Calculate total fees from transactions."""
        if transactions is None:
            transactions = self.transactions.values()
        return sum(tx.fee for tx in transactions)

    def size(self) -> int:
        """Get the number of transactions in the pool."""
        return len(self.transactions)

    def to_dict(self) -> Dict:
        """Convert pool to dictionary."""
        return {
            'size': self.size(),
            'transactions': [tx.to_dict() for tx in self.transactions.values()],
            'total_fees': self.get_total_fees()
        }
