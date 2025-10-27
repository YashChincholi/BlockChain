import time
import logging
import threading
from typing import Optional, Dict, List, Callable
from blockchain.block import Block, BlockHeader
from blockchain.merkle import MerkleTree
from blockchain.utils import meets_difficulty

logger = logging.getLogger(__name__)


class MiningJob:
    """
    Represents an active mining job.
    """

    def __init__(self, job_id: str, block: Block, difficulty: int):
        self.job_id = job_id
        self.block = block
        self.difficulty = difficulty
        self.start_time = time.time()
        self.is_cancelled = False
        self.is_complete = False
        self.result: Optional[Block] = None
        self.attempts = 0
        self.current_hash = ""

    def cancel(self):
        """Cancel the mining job."""
        self.is_cancelled = True
        logger.info(f"Mining job {self.job_id} cancelled")

    def complete(self, result: Block):
        """Mark the job as complete."""
        self.is_complete = True
        self.result = result
        logger.info(f"Mining job {self.job_id} completed")

    def get_status(self) -> Dict:
        """Get the current status of the mining job."""
        elapsed = time.time() - self.start_time
        return {
            'job_id': self.job_id,
            'is_complete': self.is_complete,
            'is_cancelled': self.is_cancelled,
            'elapsed_time': elapsed,
            'attempts': self.attempts,
            'current_hash': self.current_hash,
            'difficulty': self.difficulty,
            'block_index': self.block.index
        }


class Miner:
    """
    Handles Proof of Work mining.
    """

    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.active_jobs: Dict[str, MiningJob] = {}
        self.mining_lock = threading.Lock()
        logger.info(f"Miner initialized with difficulty {difficulty}")

    def set_difficulty(self, difficulty: int):
        """Set mining difficulty."""
        if difficulty < 0:
            raise ValueError("Difficulty must be non-negative")
        self.difficulty = difficulty
        logger.info(f"Mining difficulty set to {difficulty}")

    def mine_block(self,
                   index: int,
                   transactions: List[Dict],
                   previous_hash: str,
                   difficulty: Optional[int] = None,
                   job_id: Optional[str] = None,
                   progress_callback: Optional[Callable] = None) -> Block:
        """
        Mine a new block using Proof of Work.
        """
        if difficulty is None:
            difficulty = self.difficulty

        merkle_tree = MerkleTree(transactions)
        merkle_root = merkle_tree.get_root()

        block = Block(
            index=index,
            transactions=transactions,
            previous_hash=previous_hash,
            merkle_root=merkle_root,
            nonce=0,
            difficulty=difficulty
        )

        if job_id:
            mining_job = MiningJob(job_id, block, difficulty)
            self.active_jobs[job_id] = mining_job
        else:
            mining_job = None

        start_time = time.time()
        nonce = 0

        logger.info(f"Mining block {index} with difficulty {difficulty}")

        try:
            while True:
                if mining_job and mining_job.is_cancelled:
                    logger.info(f"Mining cancelled at nonce {nonce}")
                    raise InterruptedError("Mining cancelled")

                block.header.nonce = nonce
                current_hash = block.calculate_hash()

                if mining_job:
                    mining_job.attempts = nonce
                    mining_job.current_hash = current_hash

                if progress_callback and nonce % 1000 == 0:
                    progress_callback(nonce, current_hash)

                if meets_difficulty(current_hash, difficulty):
                    block.hash = current_hash
                    mining_time = time.time() - start_time

                    logger.info(
                        f"Block {index} mined! Hash: {current_hash[:16]}... "
                        f"Nonce: {nonce}, Time: {mining_time:.2f}s"
                    )

                    if mining_job:
                        mining_job.complete(block)

                    return block

                nonce += 1

                if nonce > 10000000:
                    logger.warning(f"Mining taking too long, reached nonce {nonce}")

        except Exception as e:
            logger.error(f"Mining error: {e}")
            if mining_job:
                mining_job.cancel()
            raise

    def mine_block_async(self,
                        index: int,
                        transactions: List[Dict],
                        previous_hash: str,
                        job_id: str,
                        difficulty: Optional[int] = None,
                        callback: Optional[Callable] = None):
        """
        Mine a block asynchronously in a background thread.
        """

        def mining_thread():
            try:
                block = self.mine_block(
                    index=index,
                    transactions=transactions,
                    previous_hash=previous_hash,
                    difficulty=difficulty,
                    job_id=job_id
                )

                if callback:
                    callback(True, block, None)

            except Exception as e:
                logger.error(f"Async mining error: {e}")
                if callback:
                    callback(False, None, str(e))

        thread = threading.Thread(target=mining_thread, daemon=True)
        thread.start()
        logger.info(f"Mining started in background thread for job {job_id}")

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get the status of a mining job."""
        job = self.active_jobs.get(job_id)
        if job:
            return job.get_status()
        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a mining job."""
        job = self.active_jobs.get(job_id)
        if job:
            job.cancel()
            return True
        return False

    def get_all_jobs(self) -> Dict[str, Dict]:
        """Get status of all mining jobs."""
        return {job_id: job.get_status() for job_id, job in self.active_jobs.items()}

    def cleanup_completed_jobs(self):
        """Remove completed jobs from the active jobs list."""
        completed = [job_id for job_id, job in self.active_jobs.items()
                    if job.is_complete or job.is_cancelled]

        for job_id in completed:
            del self.active_jobs[job_id]

        if completed:
            logger.info(f"Cleaned up {len(completed)} completed jobs")

    @staticmethod
    def verify_proof_of_work(block: Block) -> bool:
        """
        Verify that a block's hash meets its difficulty requirement.
        """
        computed_hash = block.calculate_hash()

        if computed_hash != block.hash:
            logger.warning(f"Block {block.index} hash mismatch")
            return False

        if not meets_difficulty(block.hash, block.difficulty):
            logger.warning(f"Block {block.index} does not meet difficulty {block.difficulty}")
            return False

        return True

    def estimate_time(self, difficulty: int, hash_rate: float = 1000.0) -> float:
        """
        Estimate time to mine a block based on difficulty and hash rate.
        Returns estimated time in seconds.
        """
        target_attempts = 16 ** difficulty
        return target_attempts / hash_rate
