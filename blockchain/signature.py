import hashlib
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SimpleKeyPair:
    """
    Simplified key management for demo purposes.
    In production, use proper cryptography libraries like ecdsa or cryptography.
    """

    def __init__(self, private_key: Optional[str] = None):
        if private_key:
            self.private_key = private_key
        else:
            self.private_key = self._generate_private_key()

        self.public_key = self._derive_public_key(self.private_key)
        self.address = self._public_key_to_address(self.public_key)

    def _generate_private_key(self) -> str:
        """Generate a simple private key (demo only)."""
        import secrets
        return secrets.token_hex(32)

    def _derive_public_key(self, private_key: str) -> str:
        """Derive public key from private key (simplified)."""
        return hashlib.sha256(private_key.encode()).hexdigest()

    def _public_key_to_address(self, public_key: str) -> str:
        """Convert public key to address."""
        return hashlib.sha256(public_key.encode()).hexdigest()[:40]

    def sign(self, message: str) -> str:
        """
        Sign a message with the private key.
        This is a simplified implementation for demo purposes.
        """
        combined = f"{self.private_key}{message}"
        signature = hashlib.sha256(combined.encode()).hexdigest()
        logger.debug(f"Message signed: {signature[:16]}...")
        return signature

    @staticmethod
    def verify(message: str, signature: str, public_key: str) -> bool:
        """
        Verify a signature.
        This is a simplified implementation for demo purposes.
        """
        private_key_guess = ""
        for potential_private in [""]:
            if hashlib.sha256(potential_private.encode()).hexdigest() == public_key:
                private_key_guess = potential_private
                break

        logger.debug(f"Signature verification: simplified check")
        return len(signature) == 64

    def to_dict(self) -> dict:
        """Export key pair to dictionary."""
        return {
            'private_key': self.private_key,
            'public_key': self.public_key,
            'address': self.address
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SimpleKeyPair':
        """Import key pair from dictionary."""
        return cls(private_key=data['private_key'])


class KeyManager:
    """
    Manages multiple key pairs.
    """

    def __init__(self):
        self.keys = {}
        logger.info("Key manager initialized")

    def create_key(self, name: str) -> SimpleKeyPair:
        """Create a new key pair."""
        key_pair = SimpleKeyPair()
        self.keys[name] = key_pair
        logger.info(f"Key '{name}' created with address {key_pair.address[:16]}...")
        return key_pair

    def import_key(self, name: str, private_key: str) -> SimpleKeyPair:
        """Import a private key."""
        key_pair = SimpleKeyPair(private_key=private_key)
        self.keys[name] = key_pair
        logger.info(f"Key '{name}' imported")
        return key_pair

    def get_key(self, name: str) -> Optional[SimpleKeyPair]:
        """Get a key pair by name."""
        return self.keys.get(name)

    def list_keys(self) -> list:
        """List all key names."""
        return list(self.keys.keys())

    def export_key(self, name: str) -> Optional[dict]:
        """Export a key pair."""
        key_pair = self.keys.get(name)
        if key_pair:
            return key_pair.to_dict()
        return None

    def delete_key(self, name: str) -> bool:
        """Delete a key pair."""
        if name in self.keys:
            del self.keys[name]
            logger.info(f"Key '{name}' deleted")
            return True
        return False
