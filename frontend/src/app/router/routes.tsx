import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { LegacySurface } from "../../pages/LegacySurface";
import { LoginPage } from "../../pages/LoginPage";
import { RegisterPage } from "../../pages/RegisterPage";
import { SettingsPage } from "../../pages/SettingsPage";
import { useAppStore } from "../store/useAppStore";

const paths = [
  "/dashboard", "/upload", "/processing", "/library", "/document",
  "/questions", "/question", "/review", "/chapters", "/practice",
  "/practice/session", "/practice/results", "/analytics", "/search",
  "/first-run",
] as const;

function Protected() {
  const token = useAppStore((s) => s.token);
  return token ? <LegacySurface /> : <Navigate to="/login" replace />;
}

export function AppRoutes(): ReactElement {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {paths.map((path) => <Route key={path} path={path} element={<Protected />} />)}
      <Route path="/settings" element={<Protected />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
