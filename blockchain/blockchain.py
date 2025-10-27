import logging
import os
import time
from typing import List, Dict, Tuple, Optional
from blockchain.block import Block
from blockchain.transaction import Transaction, CoinbaseTransaction, TransactionPool
from blockchain.merkle import MerkleTree
from blockchain.mining import Miner
from blockchain.persistence import PersistenceLayer

logger = logging.getLogger(__name__)


class BlockchainConfig:
    """
    Configuration for blockchain parameters.
    """
    def __init__(self):
        self.mining_difficulty = int(os.environ.get('MINING_DIFFICULTY', '4'))
        self.block_reward = float(os.environ.get('BLOCK_REWARD', '50.0'))
        self.max_supply = float(os.environ.get('MAX_SUPPLY', '21000000.0'))
        self.db_path = os.environ.get('CHAIN_DB_PATH', 'data/chain.db')
        self.enable_persistence = os.environ.get('ENABLE_PERSISTENCE', 'true').lower() == 'true'


class Blockchain:
    """
    Production-ready blockchain with PoW, transactions, persistence, and more.
    """

    def __init__(self, config: Optional[BlockchainConfig] = None):
        self.config = config or BlockchainConfig()
        self.chain: List[Block] = []
        self.transaction_pool = TransactionPool()
        self.miner = Miner(difficulty=self.config.mining_difficulty)
        self.persistence: Optional[PersistenceLayer] = None
        self.total_supply = 0.0

        if self.config.enable_persistence:
            try:
                self.persistence = PersistenceLayer(self.config.db_path)
                self._load_from_persistence()
            except Exception as e:
                logger.error(f"Failed to initialize persistence: {e}")

        if not self.chain:
            self.chain = [self.create_genesis_block()]
            if self.persistence:
                self.persistence.save_block(self.chain[0].to_dict())

        logger.info(f"Blockchain initialized with {len(self.chain)} blocks")

    def _load_from_persistence(self):
        """
        Load blockchain from persistence layer.
        """
        if not self.persistence:
            return

        try:
            chain_data = self.persistence.load_chain()
            if chain_data:
                self.chain = [Block.from_dict(block_dict) for block_dict in chain_data]
                logger.info(f"Loaded {len(self.chain)} blocks from persistence")

                is_valid, _ = self.is_chain_valid()
                if not is_valid:
                    logger.error("Loaded chain is invalid! Starting fresh.")
                    self.chain = []
                    if self.persistence:
                        self.persistence.clear_chain()

        except Exception as e:
            logger.error(f"Error loading from persistence: {e}")

    def create_genesis_block(self) -> Block:
        """
        Create the genesis block.
        """
        genesis_tx = {
            'id': 'genesis',
            'sender': 'GENESIS',
            'recipient': 'NETWORK',
            'amount': 0,
            'timestamp': 0,
            'data': 'Genesis Block - The beginning of the chain'
        }

        merkle_tree = MerkleTree([genesis_tx])

        block = Block(
            index=0,
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            timestamp=0,
            merkle_root=merkle_tree.get_root(),
            nonce=0,
            difficulty=0
        )

        block.hash = block.calculate_hash()
        logger.info(f"Genesis block created: {block.hash[:16]}...")
        return block

    def get_last_block(self) -> Block:
        """
        Get the last block in the chain.
        """
        if not self.chain:
            raise ValueError("Blockchain is empty")
        return self.chain[-1]

    def add_block(self, data: str) -> Block:
        """
        Add a simple block (backwards compatibility).
        """
        tx = {
            'id': f'tx_{len(self.chain)}_{int(time.time())}',
            'sender': 'SYSTEM',
            'recipient': 'NETWORK',
            'amount': 0,
            'timestamp': time.time(),
            'data': data.strip()
        }

        return self.mine_block([tx])

    def mine_block(self, transactions: List[Dict], miner_address: str = "MINER") -> Block:
        """
        Mine a new block with the given transactions.
        """
        if not transactions:
            raise ValueError("Cannot mine block without transactions")

        try:
            index = len(self.chain)
            previous_hash = self.get_last_block().hash

            total_fees = sum(tx.get('fee', 0) for tx in transactions)

            if self.total_supply + self.config.block_reward <= self.config.max_supply:
                coinbase = CoinbaseTransaction(
                    recipient=miner_address,
                    reward=self.config.block_reward,
                    fees=total_fees
                )
                all_transactions = [coinbase.to_dict()] + transactions
                self.total_supply += self.config.block_reward
            else:
                all_transactions = transactions
                logger.warning("Max supply reached, no block reward")

            new_block = self.miner.mine_block(
                index=index,
                transactions=all_transactions,
                previous_hash=previous_hash,
                difficulty=self.config.mining_difficulty
            )

            self.chain.append(new_block)

            if self.persistence:
                self.persistence.save_block(new_block.to_dict())

            for tx in transactions:
                tx_id = tx.get('id')
                if tx_id:
                    self.transaction_pool.remove_transaction(tx_id)

            logger.info(f"Block {index} mined and added: {new_block.hash[:16]}...")
            return new_block

        except Exception as e:
            logger.error(f"Error mining block: {e}")
            raise

    def is_chain_valid(self) -> Tuple[bool, List[int]]:
        """
        Validate the entire blockchain.
        """
        invalid_blocks = []

        try:
            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i-1]

                if current.hash != current.calculate_hash():
                    invalid_blocks.append(i)
                    logger.warning(f"Block {i} has invalid hash")

                if current.previous_hash != previous.hash:
                    invalid_blocks.append(i)
                    logger.warning(f"Block {i} has invalid previous hash link")

                if not self.miner.verify_proof_of_work(current):
                    invalid_blocks.append(i)
                    logger.warning(f"Block {i} failed PoW verification")

                if current.transactions:
                    merkle_tree = MerkleTree(current.transactions)
                    if merkle_tree.get_root() != current.merkle_root:
                        invalid_blocks.append(i)
                        logger.warning(f"Block {i} has invalid merkle root")

            is_valid = len(invalid_blocks) == 0

            if is_valid:
                logger.info("Blockchain validation: VALID")
            else:
                logger.warning(f"Blockchain validation: INVALID (blocks: {invalid_blocks})")

            return is_valid, list(set(invalid_blocks))

        except Exception as e:
            logger.error(f"Error validating blockchain: {e}")
            return False, []

    def get_chain_as_dict(self) -> List[Dict]:
        """
        Get blockchain as list of dictionaries.
        """
        return [block.to_dict() for block in self.chain]

    def get_block(self, index: int) -> Optional[Block]:
        """
        Get a specific block by index.
        """
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def get_stats(self) -> Dict:
        """
        Get blockchain statistics.
        """
        is_valid, invalid_blocks = self.is_chain_valid()

        total_transactions = sum(len(block.transactions) for block in self.chain)

        return {
            'total_blocks': len(self.chain),
            'total_transactions': total_transactions,
            'last_block_hash': self.get_last_block().hash if self.chain else None,
            'is_valid': is_valid,
            'invalid_blocks': invalid_blocks,
            'difficulty': self.config.mining_difficulty,
            'total_supply': self.total_supply,
            'max_supply': self.config.max_supply,
            'mempool_size': self.transaction_pool.size(),
            'mempool_fees': self.transaction_pool.get_total_fees()
        }

    def replace_chain(self, new_chain_data: List[Dict]) -> bool:
        """
        Replace current chain with a new one (for P2P sync).
        """
        try:
            new_chain = [Block.from_dict(block_dict) for block_dict in new_chain_data]

            if len(new_chain) <= len(self.chain):
                logger.info("New chain is not longer than current chain")
                return False

            temp_chain = self.chain
            self.chain = new_chain

            is_valid, _ = self.is_chain_valid()

            if is_valid:
                logger.info(f"Chain replaced with {len(new_chain)} blocks")
                return True
            else:
                self.chain = temp_chain
                logger.warning("New chain is invalid, keeping current chain")
                return False

        except Exception as e:
            logger.error(f"Error replacing chain: {e}")
            return False
