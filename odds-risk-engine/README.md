# Odds & Sportsbook Risk Engine

Full-stack educational sportsbook simulator built with Django REST Framework, PostgreSQL, Redis, React and TypeScript. It demonstrates bookmaker pricing and operational risk with **virtual credits only**.

## Features
- Decimal, fractional and American odds conversion
- Implied probability, overround and proportional margin removal
- Single and accumulator bet slips with immutable accepted-odds snapshots
- Virtual wallet and ledger entries
- Outcome-level liability and net exposure dashboard
- Simulated match clock, events and live odds updates over WebSockets
- Match settlement with duplicate-settlement protection
- Simulated cash-out quote and acceptance
- Docker Compose development environment

## Quick start
Copy `.env.example` to `.env`, then run:
```bash
docker compose up --build
docker compose exec api python manage.py seed_demo
```
Frontend: http://localhost:5173  
API health: http://localhost:8000/api/health/

Demo account: `demo` / `DemoPass123!` (local development only).

## Important
This is an educational prototype—not production sportsbook infrastructure. It does not implement real-money deposits, withdrawals, redeemable balances, external sportsbook feeds, or a calibrated bookmaker pricing model. Accumulator liability attribution and cash-out pricing are simplified demonstrations. Change all development secrets before sharing or deploying.
