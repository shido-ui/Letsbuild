import { apiClient } from "./client";
import type { Provider } from "../types/api";

export type ProviderInput = {
  provider_type: Provider["provider_type"];
  model_name?: string;
  base_url?: string;
  api_key?: string;
};

export async function listProviders(): Promise<Provider[]> {
  const { data } = await apiClient.get<Provider[]>("/ai/providers");
  return data;
}

export async function createProvider(input: ProviderInput): Promise<Provider> {
  const { data } = await apiClient.post<Provider>("/ai/providers", input);
  return data;
}

export async function testProvider(id: string): Promise<{ ok: boolean }> {
  const { data } = await apiClient.post<{ ok: boolean }>(`/ai/providers/${id}/test`);
  return data;
}

export async function activateProvider(id: string): Promise<Provider> {
  const { data } = await apiClient.post<Provider>(`/ai/providers/${id}/activate`);
  return data;
}

export async function disconnectProvider(id: string): Promise<Provider> {
  const { data } = await apiClient.post<Provider>(`/ai/providers/${id}/disconnect`);
  return data;
}

export async function updateProvider(id: string, input: ProviderInput): Promise<Provider> {
  const { data } = await apiClient.put<Provider>(`/ai/providers/${id}`, input);
  return data;
}

export async function deleteProvider(id: string): Promise<void> {
  await apiClient.delete(`/ai/providers/${id}`);
}
