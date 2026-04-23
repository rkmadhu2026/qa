import { create } from "zustand";

type AuthState = {
  token: string | null;
  tenantId: string | null;
  email: string | null;
  roles: string[];
  setSession: (s: { token: string; tenantId: string; email: string; roles: string[] }) => void;
  logout: () => void;
};

// In-memory only (no localStorage; keeps demo stateless-per-session)
export const useAuth = create<AuthState>((set) => ({
  token: null,
  tenantId: null,
  email: null,
  roles: [],
  setSession: ({ token, tenantId, email, roles }) =>
    set({ token, tenantId, email, roles }),
  logout: () => set({ token: null, tenantId: null, email: null, roles: [] }),
}));
