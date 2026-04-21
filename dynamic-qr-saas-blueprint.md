# Dynamic QR Payments SaaS — Full Product Blueprint

> Consolidated working document capturing all product, architecture, database, API, UX, security, and deployment details for a multi-tenant Dynamic QR SaaS (working name: **QReconcile Cloud** / **MerchantQR OS**).

---

## 1. Concept & Positioning

**Working name:** QReconcile Cloud
**Category:** Merchant payment operations SaaS
**Positioning:** Not a QR generator. A **merchant collections + reconciliation platform** built on top of dynamic UPI QR payments.

### What "Dynamic QR" means here
- **Dynamic QR** — generated per transaction, can embed amount, order/invoice ID, and expiry.
- **Static QR** — same code reused, amount entered manually by payer.
- Gateways (Razorpay, Cashfree, etc.) already expose QR creation APIs — the SaaS wins by adding the **operations, reconciliation, branch control, and reporting layer** on top.

### One-line pitch
> "We are not a QR generator. We are a merchant payment operating system built on dynamic QR."

### Target customers
- Retail chains and franchise stores
- Restaurants and cafes
- Clinics and hospitals
- Schools, institutions, training centers
- Delivery / field collection teams
- NBFC-style agent collections
- SaaS platforms needing embedded merchant collections

---

## 2. Core Business Problem

Merchants don't struggle with "how to generate a QR." They struggle with:
- Per-order collection tracking
- Branch / terminal visibility
- Missing or delayed webhooks
- Duplicate or unmatched payments
- Settlement visibility
- Refunds and audit
- Finance reconciliation

The product is therefore a **payments operations layer** over gateway QR APIs, not a thin QR UI.

---

## 3. Product Modules

| Module | Purpose |
|---|---|
| A. Tenant & merchant management | Tenant onboarding, merchant profile, branches, terminals, staff, RBAC, white-label branding |
| B. Order & invoicing | Orders, items, tax, discount, invoice numbers, PDF invoices/receipts |
| C. Dynamic QR engine | QR per order, single/multi-use, expiry, close/cancel/regenerate, branded QR |
| D. Payment orchestration | Gateway abstraction, status normalization, idempotency |
| E. Webhook ingestion | Signed verification, persistence, retry-safe processing, DLQ, dedup |
| F. Reconciliation | Order ↔ QR ↔ payment ↔ settlement mapping, mismatch detection, refunds accounting |
| G. Settlements & finance | Settlement batches, payouts, commissions, T+0/T+1 reports |
| H. Notifications | Success / failure / expiry / refund / settlement via email, SMS, WhatsApp, webhook |
| I. Reporting & analytics | Branch-/terminal-/cashier-wise collections, heatmaps, pending/expired, refunds trend |
| J. Admin control plane | Tenant lifecycle, plans, fraud review, support tooling, manual reconciliation |

---

## 4. Feature Architecture (Next-Level)

### 4.1 Core payment engine
- Dynamic QR generation (amount + order_id)
- Expiry-based QR (e.g., 5 min / 30 min)
- Single-use / multi-use QR
- Lifecycle: `created → scanned → paid → failed → expired`
- **Advanced:** partial payment, overpayment handling, retry QR, offline QR pool

### 4.2 Merchant & tenant system
```
Tenant (Company)
 ├── Branch
 │    ├── Terminal / Device
 │    └── Staff User
```
Multi-branch hierarchy, terminal-level QR tracking, RBAC (admin/cashier/auditor), white-label branding.

### 4.3 Order & invoice engine
- Create order (items, tax, discount)
- Invoice PDF generation
- Attach QR to invoice
- Auto-close order on payment
- **Advanced:** split bill, recurring QR subscriptions, EMI / partial tracking

### 4.4 Real-time payment intelligence
- Live dashboard (payments/min, pending QR)
- WebSocket auto-refresh
- **Advanced:** fraud detection (repeated scans, abnormal patterns), smart alerts

### 4.5 Reconciliation engine (biggest differentiator)
- Auto-match order_id ↔ payment_id
- Handle duplicates, missing webhooks
- Daily reconciliation report
- **Advanced:** multi-gateway reconciliation, settlement mismatch detection, bank statement matching

### 4.6 Notification engine
SMS, email, WhatsApp, webhook — triggered on payment success/failure, QR expiry, settlement completion. **Advanced:** per-tenant templates, multi-language.

### 4.7 Analytics / BI
Revenue, success rate, payment methods, branch/cashier performance, peak hours, repeat-customer rate.

### 4.8 Cashier / POS mode
```
Enter amount → Generate QR → Show screen → Customer scans → Done
```
Fast UI, sound on success, print receipt. Android POS app, Bluetooth printer, offline sync mode.

### 4.9 Integration layer
APIs for create QR / check status / webhook; integrations with ERP (Tally, SAP), CRM, accounting.

### 4.10 AI layer (EVA Agent)
- Analyze failed payments, suggest reasons (network issue, expired QR)
- Auto-trigger retry QR
- Chatbot: "Why payment failed?" / "Show today's revenue"

### 4.11 Security & compliance
PCI compliance, tokenized storage, webhook signature validation, fraud scoring, device fingerprinting, rate limiting.

### 4.12 Settlement & finance module
Settlement status, commission calculation, refund management, auto GST report, payout tracking.

### 4.13 Admin super panel
Onboard merchants, manage plans, platform revenue, fraud monitoring, system health, manual overrides.

### Feature maturity levels
- **L1 Basic:** QR generation, payment tracking, dashboard
- **L2 Serious:** multi-tenant, reconciliation, notifications, cashier mode
- **L3 Enterprise:** branch hierarchy, analytics, integrations, settlements
- **L4 Fundable:** AI agent, fraud detection, real-time intelligence, white-label

### Biggest mistake to avoid
Just building a "QR generator UI" — zero value, gateways already do that. **Your real product = Payments + Reconciliation + Operations + Intelligence.**

---

## 5. End-to-End Flow

```
Cashier / Admin creates order
        ↓
Backend creates internal payment request
        ↓
Gateway adapter creates dynamic QR
        ↓
QR shown on web / mobile / POS screen
        ↓
Customer scans via UPI app and pays
        ↓
Gateway sends webhook
        ↓
Webhook service verifies signature, stores raw event
        ↓
Payment processor normalizes event
        ↓
Reconciliation service maps payment → order + QR
        ↓
Order marked PAID
        ↓
Receipt + notification + reports updated
```

---

## 6. Architecture

### 6.1 Logical architecture
```
[ React Web ]
[ React Native / Android POS ]
          ↓
      API Gateway
          ↓
 ┌─────────────────────────────────────────┐
 │ Auth Service / Keycloak                 │
 │ Tenant Service                          │
 │ Merchant Service                        │
 │ Order Service                           │
 │ QR Service                              │
 │ Gateway Adapter Service                 │
 │ Webhook Service                         │
 │ Payment Service                         │
 │ Reconciliation Service                  │
 │ Settlement Service                      │
 │ Notification Service                    │
 │ Reporting Service                       │
 │ Admin Service                           │
 └─────────────────────────────────────────┘
          ↓
 PostgreSQL + Redis + Object Storage
          ↓
 Payment Gateway APIs
```

### 6.2 Infra architecture
```
Internet
  ↓
Cloudflare / WAF
  ↓
NGINX Ingress / API Gateway
  ↓
Kubernetes
  ├── frontend
  ├── backend services
  ├── worker deployments
  ├── redis
  ├── postgres
  ├── rabbitmq (optional)
  ├── keycloak
  ├── prometheus
  ├── grafana
  └── loki / elastic
```

### 6.3 Service split
**MVP — modular monolith**, one backend with modules: auth, tenants, merchants, orders, qr, payments, webhooks, reconciliation, reports, admin.

**Scale out later** into: `qr-service`, `webhook-service`, `payment-service`, `reconciliation-service`, `notification-service`, `reporting-service`.

---

## 7. Tenant Model

Shared app, shared database, strict row isolation for MVP and early scale.

Every business table must contain:
- `tenant_id`
- `branch_id` (where relevant)
- `created_by`, `updated_by`
- `created_at`, `updated_at`

Hierarchy:
```
Platform
 └── Tenant
      ├── Branch
      │    ├── Terminal
      │    └── Users
      ├── Orders
      ├── QR Requests
      ├── Payments
      └── Settlements
```

Large tenants can later be moved to dedicated DB / namespace.

---

## 8. Database Design

### 8.1 Core / tenant tables

```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) UNIQUE NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  plan_name VARCHAR(50),
  timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
  currency VARCHAR(10) DEFAULT 'INR',
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  branch_id UUID NULL,
  email VARCHAR(180) NOT NULL,
  full_name VARCHAR(150) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  external_auth_id VARCHAR(150),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, email)
);

CREATE TABLE roles (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(80) NOT NULL,
  description TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, name)
);

CREATE TABLE permissions (
  id UUID PRIMARY KEY,
  code VARCHAR(120) UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE role_permissions (
  role_id UUID NOT NULL REFERENCES roles(id),
  permission_id UUID NOT NULL REFERENCES permissions(id),
  PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
  user_id UUID NOT NULL REFERENCES users(id),
  role_id UUID NOT NULL REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);
```

### 8.2 Merchant structure

```sql
CREATE TABLE branches (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) NOT NULL,
  address JSONB,
  phone VARCHAR(30),
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, code)
);

CREATE TABLE terminals (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  branch_id UUID NOT NULL REFERENCES branches(id),
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) NOT NULL,
  device_type VARCHAR(50),
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, code)
);
```

### 8.3 Orders & invoices

```sql
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(150),
  phone VARCHAR(30),
  email VARCHAR(180),
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  branch_id UUID REFERENCES branches(id),
  terminal_id UUID REFERENCES terminals(id),
  customer_id UUID REFERENCES customers(id),
  order_no VARCHAR(80) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'created',
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  subtotal_amount BIGINT NOT NULL,
  tax_amount BIGINT NOT NULL DEFAULT 0,
  discount_amount BIGINT NOT NULL DEFAULT 0,
  total_amount BIGINT NOT NULL,
  paid_amount BIGINT NOT NULL DEFAULT 0,
  notes TEXT,
  expires_at TIMESTAMP NULL,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, order_no)
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  item_name VARCHAR(200) NOT NULL,
  sku VARCHAR(80),
  quantity NUMERIC(12,2) NOT NULL,
  unit_price BIGINT NOT NULL,
  tax_amount BIGINT NOT NULL DEFAULT 0,
  line_total BIGINT NOT NULL
);
```

### 8.4 QR & payments

```sql
CREATE TABLE qr_requests (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  order_id UUID NOT NULL REFERENCES orders(id),
  branch_id UUID REFERENCES branches(id),
  terminal_id UUID REFERENCES terminals(id),
  gateway VARCHAR(50) NOT NULL,
  gateway_qr_id VARCHAR(150),
  qr_type VARCHAR(30) NOT NULL DEFAULT 'dynamic',
  usage_mode VARCHAR(30) NOT NULL DEFAULT 'single_use',
  status VARCHAR(30) NOT NULL DEFAULT 'created',
  amount BIGINT NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  qr_payload TEXT,
  qr_image_url TEXT,
  expires_at TIMESTAMP NULL,
  closed_at TIMESTAMP NULL,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE payments (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  order_id UUID REFERENCES orders(id),
  qr_request_id UUID REFERENCES qr_requests(id),
  gateway VARCHAR(50) NOT NULL,
  gateway_payment_id VARCHAR(150) NOT NULL,
  gateway_order_ref VARCHAR(150),
  status VARCHAR(30) NOT NULL,
  method VARCHAR(50),
  amount BIGINT NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  paid_at TIMESTAMP NULL,
  raw_payload JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (gateway, gateway_payment_id)
);

CREATE TABLE webhook_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NULL,
  gateway VARCHAR(50) NOT NULL,
  event_type VARCHAR(120) NOT NULL,
  event_id VARCHAR(180),
  signature_valid BOOLEAN NOT NULL DEFAULT false,
  received_at TIMESTAMP NOT NULL DEFAULT now(),
  processed_at TIMESTAMP NULL,
  process_status VARCHAR(30) NOT NULL DEFAULT 'received',
  payload JSONB NOT NULL
);

CREATE TABLE settlements (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  gateway VARCHAR(50) NOT NULL,
  settlement_ref VARCHAR(150) NOT NULL,
  amount BIGINT NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  status VARCHAR(30) NOT NULL,
  settled_at TIMESTAMP NULL,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE (gateway, settlement_ref)
);

CREATE TABLE refunds (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  payment_id UUID NOT NULL REFERENCES payments(id),
  gateway VARCHAR(50) NOT NULL,
  gateway_refund_id VARCHAR(150),
  status VARCHAR(30) NOT NULL,
  amount BIGINT NOT NULL,
  reason TEXT,
  processed_at TIMESTAMP NULL,
  raw_payload JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  actor_user_id UUID,
  entity_type VARCHAR(80) NOT NULL,
  entity_id UUID,
  action VARCHAR(80) NOT NULL,
  old_value JSONB,
  new_value JSONB,
  ip_address INET,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 8.5 Indexes
```sql
CREATE INDEX idx_orders_tenant_status_created   ON orders (tenant_id, status, created_at DESC);
CREATE INDEX idx_orders_branch_created          ON orders (tenant_id, branch_id, created_at DESC);
CREATE INDEX idx_qr_requests_tenant_status      ON qr_requests (tenant_id, status, created_at DESC);
CREATE INDEX idx_payments_tenant_status_paidat  ON payments (tenant_id, status, paid_at DESC);
CREATE INDEX idx_webhook_events_gateway_status  ON webhook_events (gateway, process_status, received_at DESC);
CREATE INDEX idx_settlements_tenant_status      ON settlements (tenant_id, status, created_at DESC);
```

---

## 9. State Machines

### Order states
`created → qr_generated → pending_payment → paid | partially_paid | expired | cancelled | refunded | failed`

### QR states
`created → active → scanned → paid | expired | closed | cancelled | failed`

### Normalized payment states
`initiated → authorized → captured → failed → refunded → partial_refund → reversed → unknown`

---

## 10. API Design

### Merchant APIs

**Create order**
```
POST /api/v1/orders
{
  "branch_id": "uuid",
  "terminal_id": "uuid",
  "customer": { "name": "Raj", "phone": "9876543210" },
  "items": [
    { "item_name": "Consultation", "quantity": 1, "unit_price": 50000 }
  ],
  "discount_amount": 0,
  "tax_amount": 0,
  "notes": "Walk-in order"
}
```

**Generate dynamic QR for order**
```
POST /api/v1/orders/{order_id}/qr
{
  "gateway": "razorpay",
  "usage_mode": "single_use",
  "expires_in_seconds": 300
}
```
Response:
```json
{
  "qr_request_id": "uuid",
  "status": "active",
  "amount": 50000,
  "currency": "INR",
  "expires_at": "2026-04-18T13:20:00Z",
  "qr_image_url": "https://...",
  "qr_payload": "upi://pay?..."
}
```

**Other endpoints**
- `GET  /api/v1/qr/{qr_request_id}`
- `POST /api/v1/qr/{qr_request_id}/close`
- `GET  /api/v1/payments?status=captured&from=2026-04-01&to=2026-04-18`
- `POST /api/v1/payments/{payment_id}/refund`
- `GET  /api/v1/reconciliation/daily?date=2026-04-18`

### Webhook API
```
POST /api/v1/webhooks/{gateway}
```
Flow: verify signature → persist raw event → enqueue processing → return 200 quickly → async processor updates payment/order/reconciliation.

### Admin APIs
- `GET  /api/v1/admin/tenants`
- `POST /api/v1/admin/tenants`
- `GET  /api/v1/admin/platform/metrics`
- `GET  /api/v1/admin/support/orders/{order_id}`
- `POST /api/v1/admin/support/replay-webhook/{event_id}`

---

## 11. Gateway Adapter Contract

```python
class GatewayAdapter:
    def create_qr(self, amount, currency, order_ref, expires_at, usage_mode, metadata): ...
    def fetch_qr(self, gateway_qr_id): ...
    def close_qr(self, gateway_qr_id): ...
    def fetch_payment(self, gateway_payment_id): ...
    def create_refund(self, gateway_payment_id, amount, reason): ...
    def verify_webhook(self, headers, body): ...
    def normalize_webhook(self, body): ...
```

Supports Razorpay first, Cashfree next, then additional gateways.

---

## 12. Reconciliation Engine

### Match keys (in priority)
1. `gateway_payment_id`
2. `gateway_qr_id`
3. `order_no`
4. amount + tenant + time window
5. branch / terminal metadata

### Outputs
- matched
- partially matched
- unmatched
- duplicate
- amount mismatch
- stale pending
- manual review required

### Key jobs
- Replay missed webhooks
- Poll payment details for stale pending QR
- Detect expired-but-later-paid cases
- Auto-close stale unpaid QR
- Finance close-of-day report

---

## 13. UI Design

### 13.1 Merchant web app screens
1. Login
2. Dashboard
3. Orders
4. Create Payment Request
5. Live QR Screen
6. Payments
7. Reconciliation
8. Settlements
9. Refunds
10. Branches
11. Terminals
12. Users & Roles
13. Reports
14. Settings

### 13.2 Merchant dashboard widgets
- Today's collection
- Success rate
- Pending QR count
- Expired QR count
- Refunds today
- Settlement awaiting
- Branch-wise graph
- Payment trend by hour

### 13.3 Live QR screen
QR image, amount, expiry countdown, branch/terminal, order number, status pill (waiting / paid / expired), audible success alert, auto transition to receipt on payment.

### 13.4 Cashier / POS mode
- Keypad amount entry
- Optional customer phone
- Generate QR → fullscreen QR
- Instant "paid" sound + green success state
- Print / share receipt

### 13.5 Admin platform
Tenant onboarding, plan limits, platform MRR, support tools, incident monitoring, webhook failures, suspicious merchant patterns.

### 13.6 UI design system
- Dark + light mode
- Fintech palette: green (success), red (error), blue (primary)
- Components: cards, tables, charts, modals, status badges
- Libraries: Material UI / Ant Design, Tailwind CSS, Recharts / Chart.js

### 13.7 UX principles
- **Speed** — cashier screen < 1s load, no heavy animations
- **Clarity** — big numbers, minimal text, clear status colors
- **Real-time** — WebSockets for payment success + QR status
- **Error handling** — clear messages ("Payment failed", "QR expired")

---

## 14. Security Design

### Required controls
- Keycloak / OIDC auth
- Tenant isolation middleware
- RBAC at API and UI layers
- Webhook signature verification
- Audit log on all money-impacting actions
- Idempotency keys for create/refund calls
- Secrets in HashiCorp Vault
- API rate limiting
- IP allowlisting for admin endpoints
- PII masking in logs
- Tamper-resistant raw webhook storage

### Money-safe behaviors
- Never trust frontend "payment success" alone
- Finalize order only after verified webhook or verified payment fetch
- Store raw gateway payload for all payment state changes
- Make webhook processors idempotent

---

## 15. Tech Stack

**Backend**
- FastAPI + SQLAlchemy + Pydantic
- Celery / Dramatiq / RQ workers
- Redis (cache + short-lived locks)
- PostgreSQL (system of record)

**Frontend**
- React + TypeScript
- Tailwind
- TanStack Query
- Zustand or Redux Toolkit
- Socket-based live QR updates

**Infra**
- Kubernetes
- NGINX Ingress
- Keycloak
- Vault
- Prometheus + Grafana
- Loki or ELK
- S3 / MinIO for invoices & receipts

---

## 16. Kubernetes Deployment Model

### Namespaces
```
qr-saas-prod
qr-saas-staging
shared-observability
shared-security
```

### Workloads
`frontend`, `api`, `worker`, `scheduler`, `keycloak`, `postgres`, `redis`, `rabbitmq` (optional), `nginx-ingress` (shared)

### Config & secrets
- ConfigMaps for app config, feature flags
- Secrets for DB creds, gateway secrets, webhook secrets
- Vault Agent Injector for dynamic secret injection

### Operational requirements
- Readiness / liveness probes
- HPA for API and workers
- PodDisruptionBudgets
- Anti-affinity for critical pods
- Resource requests / limits
- Postgres backups
- Log shipping
- Alerting on webhook lag, QR failure rate, payment mismatch

---

## 17. Observability

**Metrics**
- QR created/sec
- Webhook received/sec and processing lag
- Payment success / failure rate
- QR expiry rate
- Reconciliation mismatch count
- Refund rate
- Settlement lag (hours)

**Logs** — structured JSON with: `tenant_id`, `branch_id`, `terminal_id`, `order_id`, `qr_request_id`, `payment_id`, `gateway`, `correlation_id`

**Alerts**
- Webhook signature failures spike
- Payment success rate drops below threshold
- Stale pending QR > threshold
- Unmatched payments spike
- Refund failures
- DB replication lag
- Queue backlog

---

## 18. Folder Structure

```
qr-saas/
├── apps/
│   ├── api/
│   ├── worker/
│   └── scheduler/
├── frontend/
├── libs/
│   ├── auth/
│   ├── database/
│   ├── gateway_adapters/
│   │   ├── razorpay/
│   │   └── cashfree/
│   ├── reconciliation/
│   ├── notifications/
│   └── observability/
├── infra/
│   ├── helm/
│   ├── k8s/
│   ├── terraform/
│   └── docker/
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── runbooks/
│   └── product/
└── scripts/
```

---

## 19. MVP Build Order

**Phase 1**
- Auth + tenant isolation
- Branch + terminal management
- Order creation
- One gateway integration (Razorpay)
- Dynamic QR generation
- Webhook processing
- Payment success update
- Merchant dashboard

**Phase 2**
- Reconciliation engine
- Refund handling
- Settlements view
- Reports export
- Cashier mode

**Phase 3**
- Second gateway (Cashfree)
- White-labeling
- Finance tools
- Admin support tooling
- Mobile / Android POS app

**Phase 4**
- Anomaly detection
- AI support assistant (EVA)
- ERP / accounting integrations
- Dedicated-tenant deployment option

---

## 20. Commercial Plans

**Starter**
- 1 tenant, 1 branch, 3 users
- 1 gateway
- Dashboard + exports

**Growth**
- Multiple branches
- Cashier mode
- Refunds
- RBAC
- Reconciliation reports

**Enterprise**
- White-label
- SSO
- Dedicated environment option
- Multiple gateways
- API access
- Custom settlement views
- Premium support

---

## 21. Why This Product Wins

Not the QR itself. The edges are:
- Branch hierarchy
- Cashier UX
- Webhook resilience
- Reconciliation quality
- Settlement visibility
- Tenant-safe operations
- Fast support tooling

Gateways already expose QR creation. The defensible product is the **operations + reconciliation layer** on top.

---

## 22. Recommended First Build

- React frontend
- FastAPI backend
- PostgreSQL
- Redis
- Keycloak
- Kubernetes
- Razorpay first → Cashfree second

---

## Appendix A — Broader "Missing Features" Checklist (Production-Grade App)

Applies to any multi-use SaaS platform (ITSM, LinkedEye, CRM, payments, AI agents) — not QR-specific.

1. **Authentication & identity** — OAuth2 / OIDC via Keycloak, JWT (access + refresh), MFA, SSO (Google / Azure AD / SAML).
2. **Multi-tenant architecture** — `tenant_id` on every table, DB-level isolation, tenant-aware cache keys and routing.
3. **RBAC** — roles + permissions JSON, fine-grained permissions (e.g., `create_ticket`, `assign_ticket`, `view_reports`), enforced in UI and backend.
4. **Observability stack** — Prometheus, Grafana, ELK / Loki, OpenTelemetry tracing.
5. **Notification engine** — unified email / SMS / WhatsApp / webhook / push, event-driven (Apprise-style).
6. **Background jobs / queue** — RabbitMQ or Redis, workers for email, reports, AI processing.
7. **File & document management** — S3 / MinIO upload, versioning, signed URL access.
8. **AI / automation layer (EVA)** — agent workflows: Alert → Analyze → Resolve → Notify; RAG over logs/metrics; chat interface.
9. **Audit logs & compliance** — who did what, before/after, immutable.
10. **Billing & subscription** — plans, usage tracking, Stripe integration.
11. **CI/CD + deployment** — health checks, readiness probes, feature flags.
12. **Secrets management** — HashiCorp Vault, dynamic secrets.
13. **API gateway layer** — rate limiting, auth enforcement, logging.
14. **Admin dashboard** — user mgmt, tenant metrics, system health, audit log viewer.

### Modular multi-use SaaS concept
One platform → multiple modules (enable per tenant):

| Use case | Modules |
|---|---|
| IT company | ITSM + Monitoring |
| E-commerce | CRM + Payment |
| Startup | All modules |
| DevOps team | Monitoring + AI |

---

## Appendix B — "DYB QR" Term Clarification

"DYB QR" is ambiguous. Likely meanings:
1. **"Did You Buy" QR** — informal trading/chat slang for "did you pay via scanning a QR?"
2. **Dynamic QR** — most likely intent: QR generated per transaction (UPI / Razorpay / Cashfree), embeds amount, merchant ID, transaction ID.
3. **Static QR** — same QR always, amount entered manually.

For a DevOps / backend / fintech context, "DYB QR" almost certainly means **Dynamic QR in UPI / payment systems**, which is the product this blueprint covers.

---

## Appendix C — Strong Product Name Candidates

- Qrivo
- PayPulse QR
- QReconcile
- ScanLedger
- QFlow Pay
- MerchantQR OS
