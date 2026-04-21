# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Multi-tenant Dynamic QR SaaS: merchants sign up, create orders, generate Razorpay QR codes, and receive payments via webhooks. Covers the full loop: auth → order → QR → webhook → reconciliation → cashier UI.

## Commands

### Local dev (Docker Compose — recommended)
```bash
# First-time setup
cp backend/.env.example backend/.env
# Edit backend/.env: fill RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET

docker compose -f infra/docker-compose.yml up --build
```
- API + interactive docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- The SQL migration (`backend/migrations/001_init.sql`) is auto-applied by Docker when the `db` container initialises.

### Backend (without Docker)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # runs on :8000
```
Apply the migration manually: `psql $DATABASE_URL -f migrations/001_init.sql`

### Frontend (without Docker)
```bash
cd frontend
npm install
npm run dev          # Vite dev server on :5173
npm run build        # tsc + vite build
```
Set `VITE_API_BASE=http://localhost:8000` in a `.env` file or shell to point at the API.

## Architecture

### Backend (`backend/app/`)

```
core/
  config.py       — pydantic-settings; all env vars live here (Settings singleton)
  database.py     — SQLAlchemy engine + SessionLocal + get_db dependency
  security.py     — JWT encode/decode (HS256)
  deps.py         — FastAPI dependencies: AuthContext, get_current_ctx, require_roles
models/
  _mixins.py      — UuidPk + Timestamps mixins used by every model
  tenant.py       — Tenant, User
  merchant.py     — Branch, Terminal, Customer
  order.py        — Order, OrderItem, QrRequest
  payment.py      — Payment
  audit.py        — WebhookEvent
routers/          — HTTP layer only; delegates to services
services/
  orders.py       — create_order, generate_qr (calls gateway, writes QrRequest)
  webhooks.py     — persist_event, process_event (idempotent payment upsert, order state machine)
  reconciliation.py — daily match/mismatch/duplicate engine
gateways/
  base.py         — GatewayAdapter ABC (extend this to add new payment gateways)
  razorpay.py     — Razorpay implementation; get_razorpay() returns a singleton
```

**Multi-tenancy**: every table carries `tenant_id` (UUID FK → tenants). Isolation is enforced in service code using `AuthContext.tenant_id` from the JWT (`tid` claim), not via Postgres RLS. Every route that touches tenant data must pass `tenant_id` through to the service layer.

**Auth flow**: `POST /api/v1/auth/login` issues a JWT containing `sub` (user_id), `tid` (tenant_id), `email`, `roles`. The `get_current_ctx` dependency decodes it and returns `AuthContext`. Role-gating uses `require_roles(*roles)` as a FastAPI dependency.

**Order state machine**: `created` → `qr_generated` → `paid` / `partially_paid` / `cancelled` / `refunded`. Transitions happen in `services/webhooks.py:_apply_payment`. QR generation is blocked for terminal states.

**Webhook safety**: Raw payload is persisted to `webhook_events` *before* processing. HMAC SHA-256 verification (Razorpay signature) happens in the router against the raw request body. Payment upsert is idempotent via `UNIQUE(gateway, gateway_payment_id)`. Replaying the same webhook is safe.

**Money amounts**: stored as integers in **paise** (smallest INR unit) throughout — no floating-point math.

### Frontend (`frontend/src/`)

```
lib/
  auth.ts    — Zustand store: {token, tenantId, email, roles}. In-memory only (no localStorage).
  api.ts     — Thin fetch wrapper; reads token from Zustand store; base URL from VITE_API_BASE.
pages/
  Login.tsx          — signup + login form
  Dashboard.tsx      — KPI cards (today revenue, success rate, pending QRs)
  Cashier.tsx        — create order → generate QR → countdown timer + live status poll
  Orders.tsx         — order list with status filter
  Reconciliation.tsx — daily reconciliation report
App.tsx    — React Router v6; Protected wrapper redirects unauthenticated users to /login
```

**Data fetching**: TanStack Query (`@tanstack/react-query`) for all API calls. Cashier page polls QR status via `refetchInterval` while QR is active.

**Auth state**: Zustand store is in-memory only — a browser refresh resets the session. This is an intentional demo trade-off.

**API client**: `lib/api.ts` exports a typed `api` object. Login uses `application/x-www-form-urlencoded` (OAuth2 password flow); everything else is JSON.

## Key environment variables (backend)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis URL (reserved for future queuing) |
| `JWT_SECRET` | Signing key for JWTs |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Razorpay API credentials |
| `RAZORPAY_WEBHOOK_SECRET` | HMAC secret for webhook signature verification |
| `CORS_ORIGINS` | Comma-separated allowed origins (default: `http://localhost:5173`) |

## Adding a new payment gateway

1. Create `backend/app/gateways/<name>.py` implementing all methods in `GatewayAdapter` (`base.py`).
2. Return your adapter from a `get_<name>()` factory function.
3. Update `services/orders.py` and `services/webhooks.py` to use the new gateway where `get_razorpay()` is called.
4. Add a `POST /api/v1/webhooks/<name>` router that verifies the gateway's signature and calls `persist_event` + `process_event`.
