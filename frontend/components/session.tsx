"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

const Context = createContext<{
  user: User | null; loading: boolean; loggingOut: boolean;
  setUser: (user: User | null) => void; clearForLogout: () => void;
}>({ user: null, loading: true, loggingOut: false, setUser: () => {}, clearForLogout: () => {} });
export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const pathname = usePathname();
  useEffect(() => { api<User>("/auth/me").then(setUser).catch(() => setUser(null)).finally(() => setLoading(false)); }, []);
  // Only suppress the protected-page redirect until sign-out navigation lands.
  // Later back-button/unauthenticated navigation must still reach sign-in.
  useEffect(() => { setLoggingOut(false); }, [pathname]);
  function clearForLogout() { setLoggingOut(true); setUser(null); }
  return <Context.Provider value={{ user, loading, loggingOut, setUser, clearForLogout }}>{children}</Context.Provider>;
}
export function useSession() { return useContext(Context); }
