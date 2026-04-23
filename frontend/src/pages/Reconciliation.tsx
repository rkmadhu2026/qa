import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

const paise = (p: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" })
    .format(p / 100);

export default function Reconciliation() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [tab, setTab] = useState<"matched" | "issues" | "stale_pending">("matched");

  const { data, isLoading } = useQuery({
    queryKey: ["recon", date],
    queryFn: () => api.recon(date),
  });

  if (isLoading || !data) return <div>Loading reconciliation…</div>;

  const totals = data.totals;
  const rows = (data[tab] as any[]) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-semibold">Reconciliation</h1>
        <input type="date" className="input w-48"
               value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Stat label="Orders" value={totals.orders} />
        <Stat label="Payments" value={totals.payments} />
        <Stat label="Captured" value={paise(totals.captured_amount)} />
        <Stat label="Matched" value={totals.matched} tone="green" />
        <Stat label="Issues" value={totals.issues} tone="red" />
      </div>

      <div className="flex gap-2">
        {(["matched", "issues", "stale_pending"] as const).map((t) => (
          <button key={t}
                  onClick={() => setTab(t)}
                  className={`btn ${tab === t ? "bg-brand text-white" : "bg-white border"}`}>
            {t.replace("_", " ")} ({data[t]?.length ?? 0})
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 bg-slate-50">
            <tr>
              <th className="px-4 py-2">Tag</th>
              <th className="px-4 py-2">Order</th>
              <th className="px-4 py-2">Payment ID</th>
              <th className="px-4 py-2">Amount</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r: any, i: number) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2">{badge(r.tag)}</td>
                <td className="px-4 py-2">{r.order_no || r.order_id || "—"}</td>
                <td className="px-4 py-2 font-mono text-xs">
                  {r.gateway_payment_id || "—"}
                </td>
                <td className="px-4 py-2">
                  {r.amount ? paise(r.amount) : r.total ? paise(r.total) : "—"}
                </td>
                <td className="px-4 py-2">{r.status || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: any;
                                        tone?: "green" | "red" }) {
  const color =
    tone === "green" ? "text-emerald-600"
    : tone === "red" ? "text-rose-600"
    : "text-slate-900";
  return (
    <div className="card">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function badge(tag: string) {
  const cls =
    tag === "matched" ? "badge-green"
    : tag === "stale_pending" ? "badge-yellow"
    : "badge-red";
  return <span className={cls}>{tag}</span>;
}
