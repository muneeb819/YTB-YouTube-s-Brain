import { useState, type FormEvent } from "react";
import { ApiError, api, setToken } from "../api";
import type { UserMe } from "../types";

export function AuthView({ onAuthed }: { onAuthed: (u: UserMe) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(email, password);
      }
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      onAuthed(await api.me());
    } catch (err) {
      const msg =
        err instanceof ApiError && err.status === 400 && mode === "register"
          ? "Registration failed. Try a different email or a stronger password."
          : err instanceof ApiError
            ? err.message
            : "Unable to reach the backend. Is it running on port 8000?";
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <h2>YTB — YouTube&rsquo;s Brain</h2>
        {error && <div className="error-box">{error}</div>}
        <div className="tabs">
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            onClick={() => {
              setMode("login");
              setError("");
            }}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            onClick={() => {
              setMode("register");
              setError("");
            }}
          >
            Register
          </button>
        </div>
        <form onSubmit={submit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              value={email}
              required
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              value={password}
              required
              minLength={8}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button type="submit" disabled={busy} style={{ width: "100%" }}>
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        <p className="side-note mt">
          First use? Register an account; new users are granted admin access in the
          backend by default.
        </p>
      </div>
    </div>
  );
}