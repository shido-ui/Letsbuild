import { Navigate, Outlet } from "react-router-dom";
import { useAppStore } from "../store/useAppStore";

export function RequireAuth() {
  const authenticated = useAppStore((state) => state.isAuthenticated);
  return authenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
