from blockchain.block import Block

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "Genesis Block", previous_hash="0")

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        try:
            index = len(self.chain)
            previous_hash = self.get_last_block().hash
            new_block = Block(index, data, previous_hash=previous_hash)
            self.chain.append(new_block)
        except Exception as e:
            print(f"Error adding block: {e}")

    def is_chain_valid(self):
        try:
            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i-1]

                if current.hash != current.calculate_hash():
                    return False
                if current.previous_hash != previous.hash:
                    return False
            return True
        except Exception as e:
            print(f"Error validating blockchain: {e}")
            return False
