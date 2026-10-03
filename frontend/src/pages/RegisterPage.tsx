import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { apiClient } from "../app/api/client";
import { AuthShell } from "./auth/AuthShell";

const schema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters").max(64),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters").max(128),
  confirmPassword: z.string(),
}).refine((value) => value.password === value.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      await apiClient.post("/auth/register", {
        username: data.username,
        email: data.email,
        password: data.password,
      });
      navigate("/login", { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Account creation failed");
    }
  };

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <AuthShell title="Create your account" subtitle="Your local account protects access to your ModuleIQ workspace.">
      {error && <div className="auth-error" role="alert">{error}</div>}
      <form className="auth-form" onSubmit={handleSubmit(onSubmit)}>
        <label>Username<input autoComplete="username" {...register("username")} /></label>
        {errors.username && <small>{errors.username.message}</small>}
        <label>Email<input type="email" autoComplete="email" {...register("email")} /></label>
        {errors.email && <small>{errors.email.message}</small>}
        <label>Password<input type="password" autoComplete="new-password" {...register("password")} /></label>
        {errors.password && <small>{errors.password.message}</small>}
        <label>Confirm password<input type="password" autoComplete="new-password" {...register("confirmPassword")} /></label>
        {errors.confirmPassword && <small>{errors.confirmPassword.message}</small>}
        <button className="btn primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="auth-foot">Already set up? <Link to="/login">Sign in</Link></p>
    </AuthShell>
  );
}
