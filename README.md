# Provably Fair Gaming Engine

A runnable educational portfolio project for all five phases: SHA-256 commitments, HMAC outcomes, seed rotation, Django REST API for dice/crash/Plinko, virtual-credit ledger, React UI, public verifier, history, tests and Docker.

**Virtual credits only. Not production audited.** No deposits or withdrawals.

## Run on Windows
Backend terminal:
```powershell
cd backend
py -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\\.venv\\Scripts\\python.exe manage.py migrate
.\\.venv\\Scripts\\python.exe manage.py seed_demo
.\\.venv\\Scripts\\python.exe manage.py runserver
```
Frontend terminal:
```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev
```
Open the Vite URL, usually http://localhost:5173. API is http://127.0.0.1:8000/api/.

Docker: `docker compose up --build`.

## API
`GET /api/health/`, `/api/wallet/`, `/api/seeds/current/`, `/api/games/history/`
`POST /api/seeds/client/` `{ "client_seed":"my-seed" }`
`POST /api/seeds/rotate/`
`POST /api/games/dice/play/` `{ "stake":"10.00","target":50 }`
`POST /api/games/crash/play/` `{ "stake":"10.00","cashout_at":"1.50" }`
`POST /api/games/plinko/play/` `{ "stake":"10.00","rows":12,"risk":"medium" }`
`POST /api/fairness/verify/` with `server_seed`, `commitment`, `client_seed`, `nonce`, `game_type`, optional `expected_outcome`.

Every play request must include a unique `Idempotency-Key` header. Amounts are decimal strings.

## PlayLedger
`LEDGER_MODE=local` runs a self-contained atomic virtual-credit ledger. `LEDGER_MODE=playledger` is deliberately fail-closed until the exact PlayLedger API contract and auth are configured. The existing repository API contract was not available in this workspace, so the code does not falsely claim an end-to-end remote integration. Map the adapter in `backend/game/ledger.py` to your deployed PlayLedger endpoints to finish that connection.

## Important limitations
This is a strong learning prototype, not an audited fairness product. The demo seed storage wrapper is not production-grade encryption; use KMS/envelope encryption in production. Add real authentication/authorization, immutable rule governance, rate limits, audit logging, independent RNG review and legal review before any real-money use.
