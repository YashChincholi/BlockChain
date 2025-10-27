import pytest
from blockchain.mining import Miner
from blockchain.utils import meets_difficulty


def test_miner_initialization():
    """Test miner initialization."""
    miner = Miner(difficulty=4)
    assert miner.difficulty == 4


def test_meets_difficulty():
    """Test difficulty checking."""
    assert meets_difficulty("0000abcd" + "f" * 56, 4) is True
    assert meets_difficulty("000abcde" + "f" * 56, 4) is False
    assert meets_difficulty("00abcdef" + "f" * 56, 4) is False


def test_mine_block():
    """Test block mining with low difficulty."""
    miner = Miner(difficulty=2)

    transactions = [
        {'id': 'tx1', 'sender': 'Alice', 'recipient': 'Bob', 'amount': 10}
    ]

    block = miner.mine_block(
        index=1,
        transactions=transactions,
        previous_hash="0" * 64,
        difficulty=2
    )

    assert block is not None
    assert block.difficulty == 2
    assert meets_difficulty(block.hash, 2)


def test_verify_proof_of_work():
    """Test PoW verification."""
    miner = Miner(difficulty=2)

    transactions = [
        {'id': 'tx1', 'sender': 'Alice', 'recipient': 'Bob', 'amount': 10}
    ]

    block = miner.mine_block(
        index=1,
        transactions=transactions,
        previous_hash="0" * 64,
        difficulty=2
    )

    assert miner.verify_proof_of_work(block) is True


if __name__ == '__main__':
    pytest.main([__file__])
