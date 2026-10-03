import axios from "axios";

export type RuntimeMode = "standalone" | "server";

export function getRuntimeMode(): RuntimeMode {
  const stored = localStorage.getItem("moduleiq_runtime_mode");
  if (stored === "server" || stored === "standalone") return stored;
  return Boolean((window as any).Capacitor?.isNativePlatform?.()) ? "standalone" : "server";
}

export function setRuntimeMode(mode: RuntimeMode) {
  localStorage.setItem("moduleiq_runtime_mode", mode);
}

export function defaultApiBase() {
  const native = Boolean((window as any).Capacitor?.isNativePlatform?.());
  return import.meta.env.VITE_API_BASE_URL || (native ? "http://127.0.0.1:8000/api" : "/api");
}

export function getApiBase() {
  return localStorage.getItem("moduleiq_api_base") || defaultApiBase();
}

export function setApiBase(value: string) {
  const normalized = value.trim().replace(/\/+$/, "");
  localStorage.setItem("moduleiq_api_base", normalized);
  apiClient.defaults.baseURL = normalized;
  return normalized;
}

export const apiClient = axios.create({
  baseURL: getApiBase(),
  timeout: 30_000,
  headers: { Accept: "application/json" },
});

export function setApiToken(token: string | null) {
  if (token) apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete apiClient.defaults.headers.common.Authorization;
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== "/login") {
      setApiToken(null);
      localStorage.removeItem("moduleiq-app-state");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
