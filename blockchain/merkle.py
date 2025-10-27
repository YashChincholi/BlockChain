import hashlib
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MerkleTree:
    """
    Implementation of a Merkle tree for efficient transaction verification.
    """

    def __init__(self, transactions: List[Dict]):
        """
        Build a Merkle tree from a list of transactions.
        """
        self.transactions = transactions
        self.leaves = []
        self.tree = []
        self.root = None

        if transactions:
            self._build_tree()

    def _hash(self, data: str) -> str:
        """Hash data using SHA256."""
        return hashlib.sha256(data.encode()).hexdigest()

    def _build_tree(self):
        """Build the Merkle tree from transactions."""
        if not self.transactions:
            self.root = self._hash("empty")
            return

        self.leaves = [self._hash(self._transaction_to_string(tx)) for tx in self.transactions]
        self.tree = [self.leaves[:]]

        current_level = self.leaves[:]

        while len(current_level) > 1:
            next_level = []

            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]

                parent_hash = self._hash(combined)
                next_level.append(parent_hash)

            self.tree.append(next_level)
            current_level = next_level

        self.root = current_level[0] if current_level else self._hash("empty")
        logger.debug(f"Merkle tree built with root: {self.root}")

    def _transaction_to_string(self, tx: Dict) -> str:
        """Convert transaction to string for hashing."""
        return f"{tx.get('id', '')}{tx.get('sender', '')}{tx.get('recipient', '')}{tx.get('amount', 0)}{tx.get('timestamp', '')}"

    def get_root(self) -> str:
        """Get the Merkle root hash."""
        return self.root if self.root else self._hash("empty")

    def get_proof(self, tx_index: int) -> Optional[List[Dict]]:
        """
        Generate a Merkle proof for a transaction at the given index.
        Returns a list of proof elements needed to verify the transaction.
        """
        if tx_index < 0 or tx_index >= len(self.transactions):
            logger.error(f"Invalid transaction index: {tx_index}")
            return None

        if not self.tree or not self.leaves:
            return None

        proof = []
        current_index = tx_index

        for level_idx in range(len(self.tree) - 1):
            level = self.tree[level_idx]

            if current_index % 2 == 0:
                if current_index + 1 < len(level):
                    sibling_hash = level[current_index + 1]
                    position = 'right'
                else:
                    sibling_hash = level[current_index]
                    position = 'right'
            else:
                sibling_hash = level[current_index - 1]
                position = 'left'

            proof.append({
                'hash': sibling_hash,
                'position': position
            })

            current_index = current_index // 2

        logger.debug(f"Generated proof for transaction {tx_index}: {len(proof)} steps")
        return proof

    def verify_proof(self, tx_hash: str, proof: List[Dict], root: str) -> bool:
        """
        Verify a Merkle proof.
        Returns True if the proof is valid, False otherwise.
        """
        if not proof:
            return tx_hash == root

        current_hash = tx_hash

        for proof_element in proof:
            sibling_hash = proof_element['hash']
            position = proof_element['position']

            if position == 'left':
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash

            current_hash = self._hash(combined)

        is_valid = current_hash == root
        logger.debug(f"Proof verification: {'VALID' if is_valid else 'INVALID'}")
        return is_valid

    def get_transaction_hash(self, tx_index: int) -> Optional[str]:
        """Get the hash of a transaction at the given index."""
        if tx_index < 0 or tx_index >= len(self.leaves):
            return None
        return self.leaves[tx_index]

    def to_dict(self) -> Dict:
        """Convert the Merkle tree to a dictionary for visualization."""
        return {
            'root': self.root,
            'leaves': self.leaves,
            'tree': self.tree,
            'transaction_count': len(self.transactions)
        }


def build_merkle_tree(transactions: List[Dict]) -> MerkleTree:
    """Helper function to build a Merkle tree from transactions."""
    return MerkleTree(transactions)


def verify_transaction_in_block(tx: Dict, tx_index: int, merkle_root: str, proof: List[Dict]) -> bool:
    """
    Verify that a transaction is included in a block using its Merkle proof.
    """
    tree = MerkleTree([tx])
    tx_hash = tree.get_transaction_hash(0)

    if not tx_hash:
        return False

    return tree.verify_proof(tx_hash, proof, merkle_root)
