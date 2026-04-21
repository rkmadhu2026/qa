# QR-SaaS — Full-Stack Multi-Tenant Dynamic QR Platform

Production-minded full-stack slice for the Dynamic QR SaaS blueprint.
Covers: **multi-tenant auth → order → dynamic QR (Razorpay) → webhook → reconciliation → cashier UI**.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · SQLAlchemy · Pydantic v2 · PostgreSQL · Redis |
| Gateway | Razorpay QR API |
| Frontend | React 18 · Vite · TypeScript · Tailwind · TanStack Query |
| Infra | Docker Compose (local) · Kubernetes-ready |

## Quick start (local)

```bash
cp backend/.env.example backend/.env
# Fill in RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, WEBHOOK_SECRET

docker compose -f infra/docker-compose.yml up --build
```

- API:        http://localhost:8000/docs
- Frontend:   http://localhost:5173
- Postgres:   localhost:5432 (qr / qr / qrsaas)
- Redis:      localhost:6379

## Layout

```
qr-saas/
├── backend/            FastAPI service (API + workers)
│   ├── app/
│   │   ├── core/       config, db, security, tenant middleware
│   │   ├── models/     SQLAlchemy models (multi-tenant)
│   │   ├── schemas/    Pydantic DTOs
│   │   ├── routers/    HTTP endpoints
│   │   ├── gateways/   Razorpay adapter (GatewayAdapter interface)
│   │   └── services/   Reconciliation, QR orchestration
│   └── migrations/     Raw SQL migration (001_init.sql)
├── frontend/           React + Vite + Tailwind
│   └── src/
│       ├── pages/      Login, Dashboard, Cashier, Orders, Reconciliation
│       ├── components/ QrScreen, Layout, KpiCard
│       └── lib/        api client, auth store
└── infra/              docker-compose.yml
```

## Feature coverage

| # | Feature | Status |
|---|---|---|
| 1 | Multi-tenant auth (JWT, tenant_id on every table) | ✅ |
| 2 | Branches + terminals | ✅ |
| 3 | Create order + items | ✅ |
| 4 | Generate dynamic QR via Razorpay (`POST /orders/{id}/qr`) | ✅ |
| 5 | Webhook receiver with HMAC signature verify | ✅ |
| 6 | Payment normalization + order state machine | ✅ |
| 7 | Reconciliation engine (match/unmatched/duplicate/mismatch) | ✅ |
| 8 | Merchant dashboard KPIs | ✅ |
| 9 | Cashier / Live QR screen (countdown + live status poll) | ✅ |
| 10 | SQL migration with indexes | ✅ |

## Money-safe guarantees

- Webhook receiver verifies HMAC SHA-256 signature.
- Raw event persisted before processing, so replays are safe.
- Order is only marked `paid` after gateway-confirmed payment.
- All writes use idempotency via `(gateway, gateway_payment_id)` unique constraint.
