import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiClient } from "../app/api/client";
import { useAppStore } from "../app/store/useAppStore";

export function RegisterPage() {
  const navigate = useNavigate();
  const setToken = useAppStore((s) => s.setToken);
  const setUser = useAppStore((s) => s.setUser);
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await apiClient.post("/auth/register", {
        username: form.username,
        email: form.email,
        password: form.password,
      });
      const body = new URLSearchParams({ username: form.username, password: form.password });
      const login = await apiClient.post("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      setToken(login.data.access_token);
      const me = await apiClient.get("/auth/me");
      setUser(me.data);
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="card auth-card">
        <span className="tag purple">MODULEIQ</span>
        <h1>Create account</h1>
        <p>Your workspace is isolated to your authenticated account.</p>
        {error && <p className="upload-error">{error}</p>}
        <form className="settings-form" onSubmit={submit}>
          <label>Username<input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="username" minLength={3} required /></label>
          <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} autoComplete="email" required /></label>
          <label>Password<input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" minLength={8} required /></label>
          <label>Confirm password<input type="password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} autoComplete="new-password" minLength={8} required /></label>
          <button className="btn primary" disabled={busy}>{busy ? "Creating..." : "Create account"}</button>
        </form>
        <p>Already registered? <Link to="/login">Sign in</Link></p>
      </section>
    </main>
  );
}
