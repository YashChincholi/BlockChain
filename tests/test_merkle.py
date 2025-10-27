import pytest
from blockchain.merkle import MerkleTree


def test_merkle_tree_creation():
    """Test Merkle tree creation with transactions."""
    transactions = [
        {'id': 'tx1', 'sender': 'Alice', 'recipient': 'Bob', 'amount': 10},
        {'id': 'tx2', 'sender': 'Bob', 'recipient': 'Charlie', 'amount': 5}
    ]

    tree = MerkleTree(transactions)
    assert tree.root is not None
    assert len(tree.leaves) == 2


def test_merkle_proof_generation():
    """Test Merkle proof generation."""
    transactions = [
        {'id': 'tx1', 'sender': 'Alice', 'recipient': 'Bob', 'amount': 10},
        {'id': 'tx2', 'sender': 'Bob', 'recipient': 'Charlie', 'amount': 5}
    ]

    tree = MerkleTree(transactions)
    proof = tree.get_proof(0)

    assert proof is not None
    assert isinstance(proof, list)


def test_merkle_proof_verification():
    """Test Merkle proof verification."""
    transactions = [
        {'id': 'tx1', 'sender': 'Alice', 'recipient': 'Bob', 'amount': 10},
        {'id': 'tx2', 'sender': 'Bob', 'recipient': 'Charlie', 'amount': 5}
    ]

    tree = MerkleTree(transactions)
    tx_hash = tree.get_transaction_hash(0)
    proof = tree.get_proof(0)
    root = tree.get_root()

    assert tree.verify_proof(tx_hash, proof, root) is True


def test_empty_merkle_tree():
    """Test empty Merkle tree."""
    tree = MerkleTree([])
    assert tree.root is not None


if __name__ == '__main__':
    pytest.main([__file__])
