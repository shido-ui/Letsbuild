import axios from "axios";
import { useAppStore } from "../store/useAppStore";

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

apiClient.interceptors.request.use((config) => {
  const token = useAppStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      useAppStore.getState().logout();
      window.location.assign("/login");
    }
    return Promise.reject(error);
  },
);
