import { useAuth } from "./auth";

const API = (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";

async function request<T>(
  path: string,
  init: RequestInit & { form?: Record<string, string> } = {}
): Promise<T> {
  const token = useAuth.getState().token;
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let body = init.body as BodyInit | undefined;
  if (init.form) {
    body = new URLSearchParams(init.form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (init.body && typeof init.body === "object" && !(init.body instanceof FormData)) {
    body = JSON.stringify(init.body);
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API}${path}`, { ...init, headers, body });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; tenant_id: string; user_id: string;
              email: string; roles: string[] }>(
      "/api/v1/auth/login",
      { method: "POST", form: { username: email, password } }
    ),

  signup: (b: {
    tenant_name: string; tenant_code: string; email: string;
    password: string; full_name: string;
  }) =>
    request<{ access_token: string; tenant_id: string; user_id: string;
              email: string; roles: string[] }>(
      "/api/v1/auth/signup",
      { method: "POST", body: b as any }
    ),

  kpis: () => request<{ today_revenue_paise: number; success_rate_pct: number;
                         pending_qr: number; failed_payments_today: number }>(
    "/api/v1/dashboard/kpis"),

  orders: (status?: string) =>
    request<Array<{ id: string; order_no: string; status: string;
                    total_amount: number; paid_amount: number;
                    created_at: string }>>(
      `/api/v1/orders${status ? `?status=${status}` : ""}`
    ),

  createOrder: (body: any) =>
    request<{ id: string; order_no: string; status: string;
              total_amount: number }>(
      "/api/v1/orders", { method: "POST", body }),

  createQr: (orderId: string, body: any) =>
    request<{ qr_request_id: string; order_id: string; status: string;
              amount: number; expires_at: string; qr_image_url: string;
              qr_payload: string }>(
      `/api/v1/orders/${orderId}/qr`, { method: "POST", body }),

  getQr: (qrId: string) =>
    request<{ qr_request_id: string; order_id: string; status: string;
              amount: number; expires_at: string; qr_image_url: string }>(
      `/api/v1/qr/${qrId}`),

  recon: (date?: string) =>
    request<any>(`/api/v1/reconciliation/daily${date ? `?date=${date}` : ""}`),

  payments: () =>
    request<Array<any>>("/api/v1/payments"),
};
