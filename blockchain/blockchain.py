import logging
from typing import List, Dict, Tuple
from blockchain.block import Block

logger = logging.getLogger(__name__)

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        logger.info("Blockchain initialized with genesis block")

    def create_genesis_block(self) -> Block:
        return Block(0, "Genesis Block", previous_hash="0")

    def get_last_block(self) -> Block:
        if not self.chain:
            raise ValueError("Blockchain is empty")
        return self.chain[-1]

    def add_block(self, data: str) -> Block:
        if not data or not isinstance(data, str) or not data.strip():
            raise ValueError("Block data cannot be empty")

        try:
            index = len(self.chain)
            previous_hash = self.get_last_block().hash
            new_block = Block(index, data.strip(), previous_hash=previous_hash)
            self.chain.append(new_block)
            logger.info(f"Block {index} added successfully: {data[:50]}")
            return new_block
        except Exception as e:
            logger.error(f"Error adding block: {e}")
            raise

    def is_chain_valid(self) -> Tuple[bool, List[int]]:
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

            is_valid = len(invalid_blocks) == 0
            if is_valid:
                logger.info("Blockchain validation: VALID")
            else:
                logger.warning(f"Blockchain validation: INVALID (blocks: {invalid_blocks})")

            return is_valid, invalid_blocks
        except Exception as e:
            logger.error(f"Error validating blockchain: {e}")
            return False, []

    def get_chain_as_dict(self) -> List[Dict]:
        return [block.to_dict() for block in self.chain]

    def get_stats(self) -> Dict:
        is_valid, invalid_blocks = self.is_chain_valid()
        return {
            'total_blocks': len(self.chain),
            'last_block_hash': self.get_last_block().hash if self.chain else None,
            'is_valid': is_valid,
            'invalid_blocks': invalid_blocks
        }
