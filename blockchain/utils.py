import json
import hashlib
from typing import Any, Dict


def deterministic_serialize(data: Any) -> str:
    """
    Serialize data deterministically for consistent hashing.
    Ensures that the same data always produces the same hash.
    """
    if isinstance(data, dict):
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
    elif isinstance(data, (list, tuple)):
        return json.dumps(data, separators=(',', ':'))
    elif isinstance(data, str):
        return data
    else:
        return str(data)


def hash_data(data: str) -> str:
    """
    Hash data using SHA256.
    """
    return hashlib.sha256(data.encode()).hexdigest()


def validate_hash_format(hash_string: str) -> bool:
    """
    Validate that a string is a valid SHA256 hash (64 hex characters).
    """
    if not isinstance(hash_string, str):
        return False
    if len(hash_string) != 64:
        return False
    try:
        int(hash_string, 16)
        return True
    except ValueError:
        return False


def meets_difficulty(hash_string: str, difficulty: int) -> bool:
    """
    Check if a hash meets the required difficulty (number of leading zeros).
    """
    if not validate_hash_format(hash_string):
        return False
    return hash_string.startswith('0' * difficulty)
