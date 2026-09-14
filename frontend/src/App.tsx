import { useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";
import type { UserMe } from "./types";
import { AuthView } from "./components/AuthView";
import { Dashboard } from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState<UserMe | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!getToken()) {
        setBusy(false);
        return;
      }
      try {
        const me = await api.me();
        if (!cancelled) setUser(me);
      } catch {
        setToken(null);
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (busy) {
    return (
      <div className="center" style={{ paddingTop: 80 }}>
        <div className="spinner" />
      </div>
    );
  }

  if (!user) {
    return <AuthView onAuthed={(u) => setUser(u)} />;
  }

  return (
    <Dashboard
      user={user}
      onLogout={() => {
        setToken(null);
        setUser(null);
      }}
    />
  );
}