import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

const paise = (p: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" })
    .format(p / 100);

export default function Orders() {
  const [status, setStatus] = useState<string>("");
  const { data } = useQuery({
    queryKey: ["orders", status],
    queryFn: () => api.orders(status || undefined),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Orders</h1>
      <div className="flex gap-2">
        {["", "paid", "pending_payment", "qr_generated", "failed"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatus(s)}
            className={`btn ${status === s ? "bg-brand text-white" : "bg-white border"}`}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 bg-slate-50">
            <tr>
              <th className="px-4 py-2">Order</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Total</th>
              <th className="px-4 py-2">Paid</th>
              <th className="px-4 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((o) => (
              <tr key={o.id} className="border-t">
                <td className="px-4 py-2 font-medium">{o.order_no}</td>
                <td className="px-4 py-2">{o.status}</td>
                <td className="px-4 py-2">{paise(o.total_amount)}</td>
                <td className="px-4 py-2">{paise(o.paid_amount)}</td>
                <td className="px-4 py-2 text-slate-500">
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
