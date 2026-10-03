import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiClient, setApiToken } from "../app/api/client";
import { useAppStore } from "../app/store/useAppStore";

export function LoginPage() {
  const navigate = useNavigate();
  const setToken = useAppStore((s) => s.setToken);
  const setUser = useAppStore((s) => s.setUser);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = new URLSearchParams({ username, password });
      const response = await apiClient.post("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      setApiToken(response.data.access_token);
      setToken(response.data.access_token);
      const me = await apiClient.get("/auth/me");
      setUser(me.data);
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="card auth-card">
        <span className="tag purple">MODULEIQ</span>
        <h1>Sign in</h1>
        <p>Access your knowledge workspace.</p>
        {error && <p className="upload-error">{error}</p>}
        <form className="settings-form" onSubmit={submit}>
          <label>Username or email<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
          <button className="btn primary" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        </form>
        <p>New to ModuleIQ? <Link to="/register">Create an account</Link></p>
      </section>
    </main>
  );
}
