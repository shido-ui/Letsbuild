import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { LegacySurface } from "../../pages/LegacySurface";
import { SettingsPage } from "../../pages/SettingsPage";

const paths = [
  "/dashboard", "/upload", "/processing", "/library", "/document",
  "/questions", "/question", "/review", "/chapters", "/practice",
  "/practice/session", "/practice/results", "/analytics", "/search",
  "/first-run",
] as const;

export function AppRoutes(): ReactElement {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {paths.map((path) => <Route key={path} path={path} element={<LegacySurface />} />)}
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
