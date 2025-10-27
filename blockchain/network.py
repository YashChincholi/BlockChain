import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Peer:
    """
    Represents a peer node in the network.
    """

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.url = f"http://{address}:{port}"
        self.last_seen = datetime.now()
        self.status = 'active'

    def to_dict(self) -> Dict:
        """Convert peer to dictionary."""
        return {
            'address': self.address,
            'port': self.port,
            'url': self.url,
            'last_seen': self.last_seen.isoformat(),
            'status': self.status
        }

    def __repr__(self) -> str:
        return f"Peer({self.url}, status={self.status})"


class PeerNetwork:
    """
    Manages peer-to-peer network connections.
    """

    def __init__(self):
        self.peers: Dict[str, Peer] = {}
        self.request_timeout = 5
        logger.info("Peer network initialized")

    def add_peer(self, address: str, port: int) -> Peer:
        """Add a peer to the network."""
        peer_id = f"{address}:{port}"

        if peer_id in self.peers:
            logger.info(f"Peer {peer_id} already exists")
            return self.peers[peer_id]

        peer = Peer(address, port)
        self.peers[peer_id] = peer
        logger.info(f"Peer {peer_id} added")
        return peer

    def remove_peer(self, address: str, port: int) -> bool:
        """Remove a peer from the network."""
        peer_id = f"{address}:{port}"

        if peer_id in self.peers:
            del self.peers[peer_id]
            logger.info(f"Peer {peer_id} removed")
            return True

        return False

    def get_peers(self) -> List[Peer]:
        """Get all peers."""
        return list(self.peers.values())

    def get_active_peers(self) -> List[Peer]:
        """Get only active peers."""
        return [peer for peer in self.peers.values() if peer.status == 'active']

    def broadcast_block(self, block_data: Dict) -> Dict[str, bool]:
        """
        Broadcast a new block to all peers.
        Returns a dictionary of peer_id -> success status.
        """
        results = {}

        for peer_id, peer in self.peers.items():
            try:
                response = requests.post(
                    f"{peer.url}/api/blocks/receive",
                    json=block_data,
                    timeout=self.request_timeout
                )

                if response.status_code == 200:
                    results[peer_id] = True
                    peer.last_seen = datetime.now()
                    logger.info(f"Block broadcast to {peer_id} successful")
                else:
                    results[peer_id] = False
                    logger.warning(f"Block broadcast to {peer_id} failed: {response.status_code}")

            except requests.exceptions.RequestException as e:
                results[peer_id] = False
                peer.status = 'offline'
                logger.error(f"Error broadcasting to {peer_id}: {e}")

        return results

    def sync_chain(self, peer_address: str, peer_port: int) -> Optional[List[Dict]]:
        """
        Sync blockchain from a specific peer.
        """
        peer_id = f"{peer_address}:{peer_port}"

        try:
            peer = self.peers.get(peer_id)
            if not peer:
                peer = Peer(peer_address, peer_port)

            response = requests.get(
                f"{peer.url}/api/chain",
                timeout=self.request_timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    peer.last_seen = datetime.now()
                    peer.status = 'active'
                    logger.info(f"Chain synced from {peer_id}")
                    return data.get('blockchain', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing from {peer_id}: {e}")
            if peer_id in self.peers:
                self.peers[peer_id].status = 'offline'

        return None

    def discover_peers(self, seed_peer: Peer) -> List[Peer]:
        """
        Discover more peers from a seed peer.
        """
        try:
            response = requests.get(
                f"{seed_peer.url}/api/peers",
                timeout=self.request_timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    discovered = []
                    for peer_data in data.get('peers', []):
                        peer = self.add_peer(peer_data['address'], peer_data['port'])
                        discovered.append(peer)

                    logger.info(f"Discovered {len(discovered)} peers from {seed_peer}")
                    return discovered

        except requests.exceptions.RequestException as e:
            logger.error(f"Error discovering peers from {seed_peer}: {e}")

        return []

    def health_check(self):
        """
        Check health of all peers.
        """
        for peer_id, peer in self.peers.items():
            try:
                response = requests.get(
                    f"{peer.url}/api/health",
                    timeout=self.request_timeout
                )

                if response.status_code == 200:
                    peer.status = 'active'
                    peer.last_seen = datetime.now()
                else:
                    peer.status = 'unhealthy'

            except requests.exceptions.RequestException:
                peer.status = 'offline'

        logger.info("Peer health check completed")

    def to_dict(self) -> Dict:
        """Convert network to dictionary."""
        return {
            'peer_count': len(self.peers),
            'active_peers': len(self.get_active_peers()),
            'peers': [peer.to_dict() for peer in self.peers.values()]
        }
