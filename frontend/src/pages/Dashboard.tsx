import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { KpiCard } from "../components/KpiCard";

const paise = (p: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" })
    .format(p / 100);

export default function Dashboard() {
  const { data: kpis } = useQuery({ queryKey: ["kpis"], queryFn: api.kpis,
                                    refetchInterval: 10_000 });
  const { data: orders } = useQuery({ queryKey: ["orders"],
                                      queryFn: () => api.orders() });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard label="Today revenue"
                 value={paise(kpis?.today_revenue_paise ?? 0)} />
        <KpiCard label="Success rate"
                 value={`${kpis?.success_rate_pct ?? 0}%`} />
        <KpiCard label="Pending QR"
                 value={String(kpis?.pending_qr ?? 0)} />
        <KpiCard label="Failed payments today"
                 value={String(kpis?.failed_payments_today ?? 0)} />
      </div>

      <div className="card">
        <div className="text-lg font-semibold mb-3">Recent orders</div>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">Order</th>
              <th>Status</th>
              <th>Total</th>
              <th>Paid</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {(orders ?? []).map((o) => (
              <tr key={o.id} className="border-t">
                <td className="py-2 font-medium">{o.order_no}</td>
                <td>{statusBadge(o.status)}</td>
                <td>{paise(o.total_amount)}</td>
                <td>{paise(o.paid_amount)}</td>
                <td className="text-slate-500">
                  {new Date(o.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function statusBadge(s: string) {
  const cls =
    s === "paid" ? "badge-green"
    : s === "failed" || s === "cancelled" ? "badge-red"
    : s === "partially_paid" || s === "pending_payment" ? "badge-yellow"
    : "badge-slate";
  return <span className={cls}>{s}</span>;
}
