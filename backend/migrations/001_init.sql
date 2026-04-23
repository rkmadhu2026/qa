-- QR-SaaS initial schema (multi-tenant)
-- Apply once:  psql $DATABASE_URL -f 001_init.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------- TENANTS & USERS ----------
CREATE TABLE IF NOT EXISTS tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) UNIQUE NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  plan_name VARCHAR(50),
  timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
  currency VARCHAR(10) DEFAULT 'INR',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  branch_id UUID NULL,
  email VARCHAR(180) NOT NULL,
  full_name VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  roles VARCHAR[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, email)
);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users (tenant_id);

-- ---------- MERCHANT STRUCTURE ----------
CREATE TABLE IF NOT EXISTS branches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) NOT NULL,
  address JSONB,
  phone VARCHAR(30),
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, code)
);

CREATE TABLE IF NOT EXISTS terminals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  branch_id UUID NOT NULL REFERENCES branches(id),
  name VARCHAR(150) NOT NULL,
  code VARCHAR(50) NOT NULL,
  device_type VARCHAR(50),
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, code)
);

-- ---------- ORDERS ----------
CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(150),
  phone VARCHAR(30),
  email VARCHAR(180),
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
  expires_at TIMESTAMPTZ NULL,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, order_no)
);

CREATE TABLE IF NOT EXISTS order_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  item_name VARCHAR(200) NOT NULL,
  sku VARCHAR(80),
  quantity NUMERIC(12,2) NOT NULL,
  unit_price BIGINT NOT NULL,
  tax_amount BIGINT NOT NULL DEFAULT 0,
  line_total BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items (order_id);

-- ---------- QR & PAYMENTS ----------
CREATE TABLE IF NOT EXISTS qr_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
  expires_at TIMESTAMPTZ NULL,
  closed_at TIMESTAMPTZ NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_qr_tenant_status ON qr_requests (tenant_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_qr_gateway_id ON qr_requests (gateway_qr_id);

CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
  paid_at TIMESTAMPTZ NULL,
  raw_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gateway, gateway_payment_id)
);
CREATE INDEX IF NOT EXISTS idx_payments_tenant_status ON payments (tenant_id, status, paid_at DESC);

CREATE TABLE IF NOT EXISTS webhook_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NULL,
  gateway VARCHAR(50) NOT NULL,
  event_type VARCHAR(120) NOT NULL,
  event_id VARCHAR(180),
  signature_valid BOOLEAN NOT NULL DEFAULT false,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ NULL,
  process_status VARCHAR(30) NOT NULL DEFAULT 'received',
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_webhooks_gateway_status ON webhook_events (gateway, process_status, received_at DESC);

CREATE TABLE IF NOT EXISTS settlements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  gateway VARCHAR(50) NOT NULL,
  settlement_ref VARCHAR(150) NOT NULL,
  amount BIGINT NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'INR',
  status VARCHAR(30) NOT NULL,
  settled_at TIMESTAMPTZ NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gateway, settlement_ref)
);

CREATE TABLE IF NOT EXISTS refunds (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  payment_id UUID NOT NULL REFERENCES payments(id),
  gateway VARCHAR(50) NOT NULL,
  gateway_refund_id VARCHAR(150),
  status VARCHAR(30) NOT NULL,
  amount BIGINT NOT NULL,
  reason TEXT,
  processed_at TIMESTAMPTZ NULL,
  raw_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID,
  actor_user_id UUID,
  entity_type VARCHAR(80) NOT NULL,
  entity_id UUID,
  action VARCHAR(80) NOT NULL,
  old_value JSONB,
  new_value JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_created ON audit_logs (tenant_id, created_at DESC);
