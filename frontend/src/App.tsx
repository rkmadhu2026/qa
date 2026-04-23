import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Cashier from "./pages/Cashier";
import Orders from "./pages/Orders";
import Reconciliation from "./pages/Reconciliation";
import { useAuth } from "./lib/auth";

function Protected({ children }: { children: JSX.Element }) {
  const token = useAuth((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="cashier" element={<Cashier />} />
        <Route path="orders" element={<Orders />} />
        <Route path="reconciliation" element={<Reconciliation />} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
