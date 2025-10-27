import pytest
from blockchain.blockchain import Blockchain, BlockchainConfig
from blockchain.block import Block


@pytest.fixture
def blockchain():
    """Create a test blockchain."""
    config = BlockchainConfig()
    config.enable_persistence = False
    config.mining_difficulty = 2
    return Blockchain(config)


def test_blockchain_initialization(blockchain):
    """Test blockchain initialization."""
    assert len(blockchain.chain) == 1
    assert blockchain.chain[0].index == 0


def test_add_simple_block(blockchain):
    """Test adding a simple block."""
    block = blockchain.add_block("Test block data")

    assert block.index == 1
    assert len(blockchain.chain) == 2


def test_chain_validation(blockchain):
    """Test blockchain validation."""
    blockchain.add_block("Block 1")
    blockchain.add_block("Block 2")

    is_valid, invalid_blocks = blockchain.is_chain_valid()

    assert is_valid is True
    assert len(invalid_blocks) == 0


def test_genesis_block(blockchain):
    """Test genesis block properties."""
    genesis = blockchain.chain[0]

    assert genesis.index == 0
    assert genesis.previous_hash == "0" * 64
    assert len(genesis.transactions) > 0


def test_get_last_block(blockchain):
    """Test getting the last block."""
    last_block = blockchain.get_last_block()

    assert last_block.index == 0

    blockchain.add_block("New block")
    last_block = blockchain.get_last_block()

    assert last_block.index == 1


def test_block_linking(blockchain):
    """Test that blocks are properly linked."""
    block1 = blockchain.add_block("Block 1")
    block2 = blockchain.add_block("Block 2")

    assert block2.previous_hash == block1.hash


if __name__ == '__main__':
    pytest.main([__file__])
