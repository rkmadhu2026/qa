import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

type Mode = "login" | "signup";

export default function Login() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [tenantCode, setTenantCode] = useState("");
  const [fullName, setFullName] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const setSession = useAuth((s) => s.setSession);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = mode === "login"
        ? await api.login(email, password)
        : await api.signup({
            tenant_name: tenantName,
            tenant_code: tenantCode,
            email, password, full_name: fullName,
          });
      setSession({
        token: res.access_token,
        tenantId: res.tenant_id,
        email: res.email,
        roles: res.roles,
      });
      navigate("/");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={submit} className="card w-full max-w-md space-y-4">
        <h1 className="text-2xl font-semibold">
          {mode === "login" ? "Merchant login" : "Create tenant"}
        </h1>
        {mode === "signup" && (
          <>
            <input className="input" placeholder="Company name"
                   value={tenantName}
                   onChange={(e) => setTenantName(e.target.value)} required />
            <input className="input" placeholder="Tenant code (short slug)"
                   value={tenantCode}
                   onChange={(e) => setTenantCode(e.target.value)} required />
            <input className="input" placeholder="Your full name"
                   value={fullName}
                   onChange={(e) => setFullName(e.target.value)} required />
          </>
        )}
        <input className="input" type="email" placeholder="Email"
               value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="input" type="password" placeholder="Password"
               value={password}
               onChange={(e) => setPassword(e.target.value)} required />
        {err && <div className="text-rose-600 text-sm">{err}</div>}
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? "Please wait…" : mode === "login" ? "Log in" : "Create & sign in"}
        </button>
        <button type="button"
                className="w-full text-sm text-slate-600 hover:underline"
                onClick={() => setMode(mode === "login" ? "signup" : "login")}>
          {mode === "login"
            ? "No tenant yet? Create one"
            : "Already have a tenant? Log in"}
        </button>
      </form>
    </div>
  );
}
