# Quick Start Guide

## Installation (30 seconds)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open browser: http://127.0.0.1:5000

## Quick Commands

### Add a block
```bash
# Via web interface:
# Click "Add New Block" → Enter data → Submit

# Via API:
curl -X POST http://localhost:5000/api/add \
  -H "Content-Type: application/json" \
  -d '{"data": "My first transaction"}'
```

### Create transaction
```bash
curl -X POST http://localhost:5000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"sender": "Alice", "recipient": "Bob", "amount": 10, "fee": 0.1}'
```

### Mine a block
```bash
curl -X POST http://localhost:5000/api/mine \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Get blockchain
```bash
curl http://localhost:5000/api/chain | jq
```

### Validate chain
```bash
curl http://localhost:5000/api/validate
```

## Configuration

Edit `.env` file:

```bash
MINING_DIFFICULTY=4      # Lower = faster mining
BLOCK_REWARD=50.0        # Reward per block
ENABLE_PERSISTENCE=true  # Save to database
```

## Common Tasks

### Adjust mining speed
```bash
# Fast (testing):
export MINING_DIFFICULTY=2

# Moderate (demo):
export MINING_DIFFICULTY=4

# Slow (realistic):
export MINING_DIFFICULTY=6
```

### Reset blockchain
```bash
rm data/chain.db
python run.py
```

### View logs
```bash
tail -f logs/blockchain.log
```

### Run tests
```bash
pip install pytest
pytest tests/ -v
```

## Architecture Overview

```
User Request
    ↓
Flask Routes (app/routes.py)
    ↓
Blockchain Logic (blockchain/blockchain.py)
    ↓
    ├─→ Mining (blockchain/mining.py)
    ├─→ Merkle Trees (blockchain/merkle.py)
    ├─→ Transactions (blockchain/transaction.py)
    ├─→ Persistence (blockchain/persistence.py)
    └─→ Network (blockchain/network.py)
    ↓
SQLite Database (data/chain.db)
```

## Key Features

| Feature | Status | Files |
|---------|--------|-------|
| Block Header/Body | ✓ | `blockchain/block.py` |
| Merkle Trees | ✓ | `blockchain/merkle.py` |
| Proof of Work | ✓ | `blockchain/mining.py` |
| Transactions | ✓ | `blockchain/transaction.py` |
| Persistence | ✓ | `blockchain/persistence.py` |
| P2P Network | ✓ | `blockchain/network.py` |
| Digital Signatures | ✓ | `blockchain/signature.py` |
| REST API | ✓ | `app/api.py` |

## Troubleshooting

### Port 5000 in use
```bash
# Option 1: Change port in run.py
# Option 2: Kill process
lsof -ti:5000 | xargs kill
```

### Module not found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Mining too slow
```bash
export MINING_DIFFICULTY=2
```

### Database locked
```bash
rm data/chain.db
```

## Production Deployment

```bash
# Install gunicorn
pip install gunicorn

# Run production server
gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chain` | Get blockchain |
| GET | `/api/blocks/<index>` | Get block |
| POST | `/api/transactions` | Create transaction |
| POST | `/api/mine` | Start mining |
| GET | `/api/mine/status/<id>` | Mining status |
| GET | `/api/mempool` | Get mempool |
| GET/POST | `/api/peers` | Manage peers |
| GET/POST | `/api/keys` | Manage keys |
| GET | `/api/health` | Health check |

## Next Steps

1. Add blocks via web interface
2. Create transactions via API
3. Mine blocks and see PoW in action
4. Explore Merkle trees and proofs
5. Set up P2P with multiple instances
6. Read full docs in README.md

## Support

For detailed documentation, see `README.md`
For feature list, see `FEATURES.md`
For API docs, see `README.md` API section

---

**Happy Blockchain Building!**
