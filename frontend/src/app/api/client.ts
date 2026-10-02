import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

export const apiClient = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { Accept: "application/json" },
});

export function setApiToken(token: string | null) {
  if (token) apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete apiClient.defaults.headers.common.Authorization;
}
