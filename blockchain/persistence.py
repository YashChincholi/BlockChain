import sqlite3
import json
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PersistenceLayer:
    """
    Handles blockchain persistence using SQLite with JSON fallback.
    """

    def __init__(self, db_path: str = "data/chain.db"):
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        self.json_backup_path = os.path.join(self.db_dir, "chain_backup.json")
        self.connection = None
        self.use_sqlite = True

        self._ensure_data_directory()
        self._initialize()

    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        if self.db_dir and not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            logger.info(f"Created data directory: {self.db_dir}")

    def _initialize(self):
        """Initialize database connection and schema."""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            self.use_sqlite = True
            logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}. Falling back to JSON.")
            self.use_sqlite = False

    def _create_tables(self):
        """Create database tables if they don't exist."""
        if not self.connection:
            return

        cursor = self.connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                index_num INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                previous_hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                nonce INTEGER DEFAULT 0,
                difficulty INTEGER DEFAULT 0,
                hash TEXT NOT NULL UNIQUE,
                transactions TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE,
                port INTEGER NOT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_block_hash ON blocks(hash)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_block_timestamp ON blocks(timestamp)
        ''')

        self.connection.commit()
        logger.info("Database tables created/verified")

    def save_block(self, block_dict: Dict) -> bool:
        """Save a block to the database."""
        if self.use_sqlite and self.connection:
            return self._save_block_sqlite(block_dict)
        else:
            return self._save_block_json(block_dict)

    def _save_block_sqlite(self, block_dict: Dict) -> bool:
        """Save block to SQLite."""
        try:
            cursor = self.connection.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO blocks
                (index_num, timestamp, previous_hash, merkle_root, nonce, difficulty, hash, transactions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                block_dict['index'],
                block_dict['timestamp'],
                block_dict['previous_hash'],
                block_dict.get('merkle_root', ''),
                block_dict.get('nonce', 0),
                block_dict.get('difficulty', 0),
                block_dict['hash'],
                json.dumps(block_dict.get('transactions', [])),
                json.dumps(block_dict.get('metadata', {}))
            ))

            self.connection.commit()
            logger.info(f"Block {block_dict['index']} saved to SQLite")
            return True

        except Exception as e:
            logger.error(f"Error saving block to SQLite: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def _save_block_json(self, block_dict: Dict) -> bool:
        """Save block to JSON file (fallback)."""
        try:
            chain = self.load_chain()
            chain.append(block_dict)

            with open(self.json_backup_path, 'w') as f:
                json.dump(chain, f, indent=2)

            logger.info(f"Block {block_dict['index']} saved to JSON")
            return True

        except Exception as e:
            logger.error(f"Error saving block to JSON: {e}")
            return False

    def load_chain(self) -> List[Dict]:
        """Load the entire blockchain."""
        if self.use_sqlite and self.connection:
            return self._load_chain_sqlite()
        else:
            return self._load_chain_json()

    def _load_chain_sqlite(self) -> List[Dict]:
        """Load chain from SQLite."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM blocks ORDER BY index_num ASC')
            rows = cursor.fetchall()

            chain = []
            for row in rows:
                block_dict = {
                    'index': row['index_num'],
                    'timestamp': row['timestamp'],
                    'previous_hash': row['previous_hash'],
                    'merkle_root': row['merkle_root'],
                    'nonce': row['nonce'],
                    'difficulty': row['difficulty'],
                    'hash': row['hash'],
                    'transactions': json.loads(row['transactions']),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                chain.append(block_dict)

            logger.info(f"Loaded {len(chain)} blocks from SQLite")
            return chain

        except Exception as e:
            logger.error(f"Error loading chain from SQLite: {e}")
            return []

    def _load_chain_json(self) -> List[Dict]:
        """Load chain from JSON file (fallback)."""
        try:
            if os.path.exists(self.json_backup_path):
                with open(self.json_backup_path, 'r') as f:
                    chain = json.load(f)
                logger.info(f"Loaded {len(chain)} blocks from JSON")
                return chain
            return []

        except Exception as e:
            logger.error(f"Error loading chain from JSON: {e}")
            return []

    def get_block(self, index: int) -> Optional[Dict]:
        """Get a specific block by index."""
        if self.use_sqlite and self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute('SELECT * FROM blocks WHERE index_num = ?', (index,))
                row = cursor.fetchone()

                if row:
                    return {
                        'index': row['index_num'],
                        'timestamp': row['timestamp'],
                        'previous_hash': row['previous_hash'],
                        'merkle_root': row['merkle_root'],
                        'nonce': row['nonce'],
                        'difficulty': row['difficulty'],
                        'hash': row['hash'],
                        'transactions': json.loads(row['transactions']),
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    }

            except Exception as e:
                logger.error(f"Error getting block {index}: {e}")

        chain = self.load_chain()
        for block in chain:
            if block['index'] == index:
                return block

        return None

    def clear_chain(self) -> bool:
        """Clear the entire blockchain (use with caution)."""
        try:
            if self.use_sqlite and self.connection:
                cursor = self.connection.cursor()
                cursor.execute('DELETE FROM blocks')
                self.connection.commit()

            if os.path.exists(self.json_backup_path):
                os.remove(self.json_backup_path)

            logger.warning("Blockchain cleared!")
            return True

        except Exception as e:
            logger.error(f"Error clearing blockchain: {e}")
            return False

    def snapshot(self, snapshot_path: str) -> bool:
        """Create a snapshot of the current blockchain."""
        try:
            chain = self.load_chain()
            with open(snapshot_path, 'w') as f:
                json.dump(chain, f, indent=2)

            logger.info(f"Snapshot created at {snapshot_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get persistence layer statistics."""
        return {
            'backend': 'sqlite' if self.use_sqlite else 'json',
            'db_path': self.db_path,
            'block_count': len(self.load_chain()),
            'connection_status': 'connected' if self.connection else 'disconnected'
        }

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
