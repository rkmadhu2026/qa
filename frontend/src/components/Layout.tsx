import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/cashier", label: "Cashier" },
  { to: "/orders", label: "Orders" },
  { to: "/reconciliation", label: "Reconciliation" },
];

export default function Layout() {
  const { email, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-slate-900 text-slate-100 p-5 flex flex-col">
        <div className="text-xl font-bold text-white mb-8">QR-SaaS</div>
        <nav className="flex-1 space-y-1">
          {navItems.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm ${
                  isActive ? "bg-brand text-white" : "hover:bg-slate-800"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="text-xs text-slate-400 mt-6">
          <div className="truncate">{email}</div>
          <button
            onClick={() => { logout(); navigate("/login"); }}
            className="mt-2 text-rose-300 hover:underline"
          >
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
