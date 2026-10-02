import type { ReactElement } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { LegacySurface } from "../../pages/LegacySurface";

const paths = [
  "/dashboard", "/upload", "/processing", "/library", "/document",
  "/questions", "/question", "/review", "/chapters", "/practice",
  "/practice/session", "/practice/results", "/analytics", "/search",
  "/settings", "/first-run",
] as const;

export function AppRoutes(): ReactElement {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {paths.map((path) => <Route key={path} path={path} element={<LegacySurface />} />)}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
