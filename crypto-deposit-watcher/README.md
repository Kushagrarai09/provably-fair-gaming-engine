# Crypto Deposit Watcher (Sepolia testnet only)

A Django REST Framework learning project that scans Ethereum Sepolia for native ETH deposits, waits for confirmations, records an internal ledger credit once, and provides a guarded withdrawal approval queue.

> **Testnet only.** This project is not audited and is not suitable for real funds. Do not use production RPC endpoints, seed phrases, or private keys. Withdrawals are approval workflow records only; this starter does not sign or broadcast transactions.

## Phases included

1. **Foundation:** Django, PostgreSQL, models, admin, API, test configuration, environment variables.
2. **Chain watcher:** JSON-RPC block scanning, native ETH transfer detection, persisted checkpoints, confirmation tracking, retry loop.
3. **Ledger integration:** atomic deposit credit, database uniqueness/idempotency, balance endpoint, tests for duplicate credit and withdrawal reservation.
4. **Reliability:** stored block hashes, canonical-chain/receipt checks, reorg state, structured Python logging, retry-on-failure behavior.
5. **Withdrawals:** idempotency key, atomic balance reservation, configurable test ETH ceiling, one/two reviewer approval thresholds, authorization.

## Requirements

- Docker Desktop (recommended) or Python 3.12+
- A Sepolia RPC URL from a provider
- Test ETH from a faucet (never real funds)

## Run on Windows with Docker

1. Copy `.env.example` to `.env`.
2. Set `ETH_RPC_URL` to a Sepolia RPC endpoint, leave `EXPECTED_CHAIN_ID=11155111`, and replace `DJANGO_SECRET_KEY` locally.
3. Run:

```powershell
docker compose up --build -d
docker compose exec api python manage.py createsuperuser
```

4. Open `http://localhost:8001/admin/`. API endpoints are under `http://localhost:8001/api/`.

## API

- `GET /api/health/` — authenticated health check.
- `GET /api/deposit-addresses/` — current user's active addresses.
- `GET /api/deposits/` — current user's deposit history.
- `GET /api/balance/` — available internal balance in wei and ETH.
- `POST /api/dev/deposit-addresses/` — staff-only helper to register a public test address.
- `POST /api/withdrawals/` — request a testnet withdrawal.
- `GET /api/withdrawals/` — list withdrawal requests.
- `POST /api/withdrawals/{id}/approve/` — staff approval; larger requests require two distinct reviewers.

## Tests

```powershell
pytest
```

Tests cover idempotent deposit credits, refusing to credit unconfirmed deposits, and idempotent withdrawal reservation. The project has not been verified against a live Sepolia RPC.

## Current limitations and safety boundaries

- Native ETH top-level transaction scanning only; no ERC-20 Transfer log or internal contract transfer scanning.
- HD wallet derivation and transaction signing are not wired in. Deposit addresses are registered as public addresses for local testing.
- Withdrawals are reserved and approved but not broadcast.
- Reorgs before credit are marked `REORGED`; a reorg affecting an already credited deposit requires manual ledger reconciliation.
- For separate PlayLedger integration, add a transactional outbox and idempotent receiver rather than relying on a fragile dual write.
- This is a learning prototype, not audited or production-ready. Never use real funds.

## Suggested extensions

1. Transactional outbox for integration with PlayLedger.
2. HD address derivation with a vetted library and secure seed custody.
3. ERC-20 log scanning and token decimals.
4. Reorg simulation and metrics.
5. Isolated testnet withdrawal signer and broadcaster.
