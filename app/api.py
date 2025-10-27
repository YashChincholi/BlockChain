import logging
import uuid
from flask import Blueprint, jsonify, request
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from blockchain.merkle import MerkleTree
from blockchain.signature import KeyManager
from blockchain.network import PeerNetwork

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__, url_prefix='/api')

blockchain = Blockchain()
key_manager = KeyManager()
peer_network = PeerNetwork()


@api.route('/chain', methods=['GET'])
def get_chain():
    """Get the entire blockchain."""
    try:
        return jsonify({
            'success': True,
            'blockchain': blockchain.get_chain_as_dict(),
            'stats': blockchain.get_stats()
        })
    except Exception as e:
        logger.error(f"Error getting chain: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/blocks/<int:index>', methods=['GET'])
def get_block(index):
    """Get a specific block by index."""
    try:
        block = blockchain.get_block(index)

        if not block:
            return jsonify({
                'success': False,
                'error': f'Block {index} not found'
            }), 404

        merkle_tree = MerkleTree(block.transactions)

        return jsonify({
            'success': True,
            'block': block.to_dict(),
            'merkle_tree': merkle_tree.to_dict()
        })

    except Exception as e:
        logger.error(f"Error getting block {index}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/transactions', methods=['POST'])
def create_transaction():
    """Create and add a transaction to the mempool."""
    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        sender = data.get('sender')
        recipient = data.get('recipient')
        amount = data.get('amount')
        fee = data.get('fee', 0.0)

        if not all([sender, recipient, amount]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: sender, recipient, amount'
            }), 400

        transaction = Transaction(
            sender=sender,
            recipient=recipient,
            amount=float(amount),
            fee=float(fee)
        )

        if blockchain.transaction_pool.add_transaction(transaction):
            return jsonify({
                'success': True,
                'message': 'Transaction added to mempool',
                'transaction': transaction.to_dict(),
                'mempool_size': blockchain.transaction_pool.size()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add transaction to mempool'
            }), 500

    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/mine', methods=['POST'])
def start_mining():
    """Start mining a new block."""
    try:
        data = request.json or {}

        transactions = data.get('transactions', [])

        if not transactions:
            mempool_txs = blockchain.transaction_pool.get_transactions(limit=10)
            transactions = [tx.to_dict() for tx in mempool_txs]

        if not transactions:
            return jsonify({
                'success': False,
                'error': 'No transactions available to mine'
            }), 400

        miner_address = data.get('miner_address', 'DEFAULT_MINER')
        job_id = str(uuid.uuid4())

        def mining_callback(success, block, error):
            if success:
                logger.info(f"Mining job {job_id} completed successfully")
            else:
                logger.error(f"Mining job {job_id} failed: {error}")

        blockchain.miner.mine_block_async(
            index=len(blockchain.chain),
            transactions=transactions,
            previous_hash=blockchain.get_last_block().hash,
            job_id=job_id,
            callback=mining_callback
        )

        return jsonify({
            'success': True,
            'message': 'Mining started',
            'job_id': job_id
        })

    except Exception as e:
        logger.error(f"Error starting mining: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/mine/status/<job_id>', methods=['GET'])
def get_mining_status(job_id):
    """Get the status of a mining job."""
    try:
        status = blockchain.miner.get_job_status(job_id)

        if not status:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        return jsonify({
            'success': True,
            'status': status
        })

    except Exception as e:
        logger.error(f"Error getting mining status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/mine/cancel/<job_id>', methods=['POST'])
def cancel_mining(job_id):
    """Cancel a mining job."""
    try:
        if blockchain.miner.cancel_job(job_id):
            return jsonify({
                'success': True,
                'message': 'Mining job cancelled'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found or already completed'
            }), 404

    except Exception as e:
        logger.error(f"Error cancelling mining: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/verify/tx-proof', methods=['POST'])
def verify_tx_proof():
    """Verify a Merkle proof for a transaction."""
    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        tx_hash = data.get('tx_hash')
        proof = data.get('proof')
        merkle_root = data.get('merkle_root')

        if not all([tx_hash, proof, merkle_root]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        merkle_tree = MerkleTree([])
        is_valid = merkle_tree.verify_proof(tx_hash, proof, merkle_root)

        return jsonify({
            'success': True,
            'is_valid': is_valid
        })

    except Exception as e:
        logger.error(f"Error verifying proof: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/mempool', methods=['GET'])
def get_mempool():
    """Get current mempool status."""
    try:
        return jsonify({
            'success': True,
            'mempool': blockchain.transaction_pool.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting mempool: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/peers', methods=['GET'])
def get_peers():
    """Get all peers."""
    try:
        return jsonify({
            'success': True,
            'peers': [peer.to_dict() for peer in peer_network.get_peers()]
        })
    except Exception as e:
        logger.error(f"Error getting peers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/peers', methods=['POST'])
def add_peer():
    """Add a new peer."""
    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        address = data.get('address')
        port = data.get('port')

        if not all([address, port]):
            return jsonify({
                'success': False,
                'error': 'Missing address or port'
            }), 400

        peer = peer_network.add_peer(address, int(port))

        return jsonify({
            'success': True,
            'message': 'Peer added',
            'peer': peer.to_dict()
        })

    except Exception as e:
        logger.error(f"Error adding peer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/peers/sync', methods=['POST'])
def sync_from_peer():
    """Sync blockchain from a peer."""
    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        address = data.get('address')
        port = data.get('port')

        if not all([address, port]):
            return jsonify({
                'success': False,
                'error': 'Missing address or port'
            }), 400

        chain_data = peer_network.sync_chain(address, int(port))

        if chain_data:
            if blockchain.replace_chain(chain_data):
                return jsonify({
                    'success': True,
                    'message': 'Chain synced successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to replace chain'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to sync from peer'
            }), 500

    except Exception as e:
        logger.error(f"Error syncing from peer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/keys', methods=['POST'])
def create_key():
    """Create a new key pair."""
    try:
        data = request.json or {}
        name = data.get('name', f'key_{uuid.uuid4().hex[:8]}')

        key_pair = key_manager.create_key(name)

        return jsonify({
            'success': True,
            'message': 'Key created',
            'key': {
                'name': name,
                'address': key_pair.address,
                'public_key': key_pair.public_key
            }
        })

    except Exception as e:
        logger.error(f"Error creating key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/keys', methods=['GET'])
def list_keys():
    """List all keys."""
    try:
        keys = []
        for name in key_manager.list_keys():
            key_pair = key_manager.get_key(name)
            if key_pair:
                keys.append({
                    'name': name,
                    'address': key_pair.address,
                    'public_key': key_pair.public_key
                })

        return jsonify({
            'success': True,
            'keys': keys
        })

    except Exception as e:
        logger.error(f"Error listing keys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/persistence/status', methods=['GET'])
def get_persistence_status():
    """Get persistence layer status."""
    try:
        if blockchain.persistence:
            stats = blockchain.persistence.get_stats()
            return jsonify({
                'success': True,
                'persistence': stats
            })
        else:
            return jsonify({
                'success': True,
                'persistence': {
                    'backend': 'none',
                    'status': 'disabled'
                }
            })

    except Exception as e:
        logger.error(f"Error getting persistence status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'stats': blockchain.get_stats()
    })
