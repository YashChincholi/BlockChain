import hashlib
import time

class Block:
    def __init__(self, index, data, timestamp=None, previous_hash="0"):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        try:
            block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}"
            return hashlib.sha256(block_string.encode()).hexdigest()
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return None
