import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

type Qr = Awaited<ReturnType<typeof api.createQr>>;

export default function Cashier() {
  const [amount, setAmount] = useState<string>(""); // rupees
  const [phone, setPhone] = useState("");
  const [qr, setQr] = useState<Qr | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const audio = useRef<HTMLAudioElement | null>(null);

  // Poll QR status while active
  const { data: status } = useQuery({
    queryKey: ["qr", qr?.qr_request_id],
    queryFn: () => api.getQr(qr!.qr_request_id),
    enabled: !!qr,
    refetchInterval: 2000,
  });

  useEffect(() => {
    if (status?.status === "paid") {
      audio.current?.play().catch(() => {});
    }
  }, [status?.status]);

  async function generate() {
    setErr(null);
    setBusy(true);
    try {
      const rupees = Number(amount);
      if (!rupees || rupees <= 0) throw new Error("Enter a valid amount");
      const paise = Math.round(rupees * 100);
      const order = await api.createOrder({
        items: [{ item_name: "Counter sale", quantity: 1,
                  unit_price: paise, tax_amount: 0 }],
        customer: phone ? { phone } : undefined,
      });
      const newQr = await api.createQr(order.id, {
        gateway: "razorpay",
        usage_mode: "single_use",
        expires_in_seconds: 300,
        customer_phone: phone || undefined,
      });
      setQr(newQr);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setQr(null);
    setAmount("");
    setPhone("");
    setErr(null);
  }

  const paidNow = status?.status === "paid";
  const expiresAt = status?.expires_at ? new Date(status.expires_at) : null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Cashier</h1>

      {!qr ? (
        <div className="card max-w-md space-y-4">
          <label className="block">
            <span className="text-sm text-slate-600">Amount (₹)</span>
            <input
              className="input mt-1 text-2xl font-semibold"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              autoFocus
            />
          </label>
          <label className="block">
            <span className="text-sm text-slate-600">Customer phone (optional)</span>
            <input
              className="input mt-1"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="98xxxxxxxx"
            />
          </label>
          {err && <div className="text-rose-600 text-sm">{err}</div>}
          <button onClick={generate} disabled={busy}
                  className="btn-primary w-full text-lg">
            {busy ? "Generating…" : "Generate QR"}
          </button>
        </div>
      ) : (
        <div className="card max-w-lg text-center space-y-4">
          <div className="text-slate-500">Order {qr.order_id.slice(0, 8)}</div>
          <div className="text-5xl font-bold">₹{(qr.amount / 100).toFixed(2)}</div>

          {qr.qr_image_url ? (
            <img
              src={qr.qr_image_url}
              alt="QR"
              className={`mx-auto h-72 w-72 rounded-xl border ${
                paidNow ? "opacity-30" : ""
              }`}
            />
          ) : (
            <div className="text-sm text-slate-500">(QR image not returned by gateway)</div>
          )}

          <Countdown until={expiresAt} />

          <div>
            {paidNow ? (
              <span className="badge-green text-base">✓ PAID</span>
            ) : status?.status === "expired" ? (
              <span className="badge-red text-base">Expired</span>
            ) : (
              <span className="badge-yellow text-base">
                Waiting for payment…
              </span>
            )}
          </div>

          <div className="flex gap-3 justify-center">
            <button className="btn-ghost" onClick={reset}>New sale</button>
          </div>
          <audio ref={audio} src="data:audio/wav;base64,UklGRrwAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YZgAAAAA" />
        </div>
      )}
    </div>
  );
}

function Countdown({ until }: { until: Date | null }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!until) return null;
  const sec = Math.max(0, Math.floor((until.getTime() - now) / 1000));
  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return <div className="text-sm text-slate-500">Expires in {mm}:{ss}</div>;
}
