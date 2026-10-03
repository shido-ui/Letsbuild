import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { apiClient } from "../app/api/client";
import { useAppStore } from "../app/store/useAppStore";
import { AuthShell } from "./auth/AuthShell";

const schema = z.object({
  username: z.string().min(1, "Username or email is required"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const setSession = useAppStore((state) => state.setSession);
  const [error, setError] = useState("");

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      const body = new FormData();
      body.append("username", data.username);
      body.append("password", data.password);
      const response = await apiClient.post("/auth/login", body);
      setSession(response.data.access_token, null);
      const me = await apiClient.get("/auth/me");
      setSession(response.data.access_token, me.data);
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
    }
  };

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to continue to your private knowledge workspace.">
      {error && <div className="auth-error" role="alert">{error}</div>}
      <form className="auth-form" onSubmit={handleSubmit(onSubmit)}>
        <label>Username or email<input autoComplete="username" {...register("username")} /></label>
        {errors.username && <small>{errors.username.message}</small>}
        <label>Password<input type="password" autoComplete="current-password" {...register("password")} /></label>
        {errors.password && <small>{errors.password.message}</small>}
        <button className="btn primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="auth-foot">First run? <Link to="/register">Create your local account</Link></p>
    </AuthShell>
  );
}
