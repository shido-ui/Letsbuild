export type ProviderType = "gemini" | "openai" | "openai_compatible" | "local";

export type ProviderSummary = {
  id: string;
  provider_type: ProviderType;
  model_name: string | null;
  base_url: string | null;
  enabled: boolean;
  active: boolean;
  connected: boolean;
  key_fingerprint: string | null;
};

export type ApiError = { detail?: string; message?: string };
