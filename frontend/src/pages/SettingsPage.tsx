import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { apiClient } from "../app/api/client";
import { activateProvider, createProvider, deleteProvider, disconnectProvider, listProviders, testProvider, updateProvider } from "../app/api/providers";
import type { Provider, ProviderType } from "../app/types/api";

const schema = z.object({
  provider_type: z.enum(["gemini", "openai", "openai_compatible", "local"]),
  model_name: z.string().trim().max(120).optional(),
  base_url: z.string().trim().url("Enter a valid URL").optional().or(z.literal("")),
  api_key: z.string().trim().min(1, "API key is required").optional(),
});
type FormValues = z.infer<typeof schema>;

const defaults: FormValues = {
  provider_type: "gemini",
  model_name: "gemini-2.5-flash",
  base_url: "",
  api_key: "",
};

const labels: Record<ProviderType, string> = {
  gemini: "Google Gemini",
  openai: "OpenAI",
  openai_compatible: "OpenAI-compatible",
  local: "Local model",
};

const models: Record<ProviderType, string[]> = {
  gemini: ["gemini-2.5-flash", "gemini-2.5-pro"],
  openai: ["gpt-5", "gpt-5-mini"],
  openai_compatible: ["gpt-5", "custom"],
  local: ["local"],
};

function errorMessage(error: unknown) {
  const response = (error as { response?: { data?: { detail?: string } } })?.response;
  return response?.data?.detail || (error instanceof Error ? error.message : "Something went wrong.");
}

export function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [testState, setTestState] = useState<Record<string, "testing" | "ok" | "error">>({});
  const form = useForm<FormValues>({ defaultValues: defaults });

  const providerType = form.watch("provider_type");
  const selectedModel = form.watch("model_name");
  const isLocal = providerType === "local";

  const active = useMemo(() => providers.find((p) => p.active), [providers]);

  async function refresh() {
    try {
      setProviders(await listProviders());
    } catch (error) {
      setStatus(errorMessage(error));
    }
  }

  useEffect(() => { void refresh(); }, []);

  useEffect(() => {
    const first = models[providerType][0];
    if (selectedModel && models[providerType].includes(selectedModel)) return;
    form.setValue("model_name", first);
    if (providerType === "openai") form.setValue("base_url", "https://api.openai.com/v1");
    else if (providerType === "gemini") form.setValue("base_url", "");
  }, [providerType]);

  async function onSubmit(raw: FormValues) {
    const parsed = schema.safeParse(raw);
    if (!parsed.success) {
      setStatus(parsed.error.issues[0]?.message || "Check the form.");
      return;
    }
    setBusy(true);
    setStatus("");
    try {
      if (editing) {
        await updateProvider(editing, parsed.data);
        setStatus("API key and provider settings updated and verified.");
      } else {
        await createProvider(parsed.data);
        setStatus("Provider connected and verified.");
      }
      form.reset(defaults);
      setEditing(null);
      setShowKey(false);
      await refresh();
    } catch (error) {
      setStatus(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function onTest(id: string) {
    setTestState((s) => ({ ...s, [id]: "testing" }));
    try {
      await testProvider(id);
      setTestState((s) => ({ ...s, [id]: "ok" }));
    } catch {
      setTestState((s) => ({ ...s, [id]: "error" }));
    }
  }

  async function onUse(id: string) {
    setBusy(true);
    try {
      await activateProvider(id);
      await refresh();
      setStatus("AI provider switched. Your knowledge remains independent.");
    } catch (error) {
      setStatus(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function onDisconnect(id: string) {
    setBusy(true);
    try {
      await disconnectProvider(id);
      await refresh();
      setStatus("AI disconnected. Stored knowledge remains available.");
    } catch (error) {
      setStatus(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    setBusy(true);
    try {
      await deleteProvider(id);
      await refresh();
      if (editing === id) {
        setEditing(null);
        form.reset(defaults);
      }
      setStatus("Provider removed. Its credential was deleted.");
    } catch (error) {
      setStatus(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  function startReplace(provider: Provider) {
    setEditing(provider.id);
    form.reset({
      provider_type: provider.provider_type,
      model_name: provider.model_name || models[provider.provider_type][0],
      base_url: provider.base_url || (provider.provider_type === "openai" ? "https://api.openai.com/v1" : ""),
      api_key: "",
    });
    setShowKey(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="page">
      <header>
        <div><small>Workspace /</small><b>Settings</b></div>
        <div className="top"><b className="avatar">S</b></div>
      </header>
      <main>
        <div className="title">
          <div>
            <h2>Settings</h2>
            <p>Control your AI connection without editing code, environment files, or losing your knowledge.</p>
          </div>
        </div>

        <div className="settings">
          <section className="card">
            <span className="tag purple">AI ENGINE</span>
            <h2>{editing ? "Replace API key" : "Connect an AI provider"}</h2>
            <p>Credentials are submitted to the local backend, encrypted at rest, and never included in knowledge exports.</p>

            <form onSubmit={form.handleSubmit(onSubmit)} className="settings-form">
              <label>
                Provider
                <select {...form.register("provider_type")}>
                  {(Object.keys(labels) as ProviderType[]).map((type) => <option value={type} key={type}>{labels[type]}</option>)}
                </select>
              </label>

              <label>
                Model
                <select {...form.register("model_name")}>
                  {models[providerType].map((model) => <option value={model} key={model}>{model}</option>)}
                </select>
              </label>

              {providerType === "openai_compatible" && (
                <label>
                  Base URL
                  <input placeholder="https://your-provider.example/v1" {...form.register("base_url")} />
                </label>
              )}

              {providerType === "openai" && (
                <label>
                  OpenAI endpoint
                  <input {...form.register("base_url")} />
                </label>
              )}

              {!isLocal && (
                <label>
                  API key
                  <div className="key-field">
                    <input type={showKey ? "text" : "password"} autoComplete="off" placeholder={editing ? "Enter replacement key" : "Paste your API key"} {...form.register("api_key")} />
                    <button type="button" className="btn" onClick={() => setShowKey((v) => !v)}>{showKey ? "Hide" : "Show"}</button>
                  </div>
                </label>
              )}

              {isLocal && <p className="tag green">LOCAL MODEL · No cloud credential required</p>}

              <div>
                <button className="btn primary" disabled={busy} type="submit">{busy ? "Saving..." : editing ? "Replace & verify" : "Test & connect"}</button>
                {editing && <button type="button" className="btn" onClick={() => { setEditing(null); form.reset(defaults); }}>Cancel</button>}
              </div>
            </form>
          </section>

          <section className="card">
            <div className="title">
              <div><h3>Connected providers</h3><p>{active ? <>Active: <b>{labels[active.provider_type]}</b></> : "No provider is currently active."}</p></div>
            </div>
            {providers.length === 0 && <p>No provider configured yet. Add one above when you want AI assistance.</p>}
            {providers.map((provider) => (
              <div className="provider" key={provider.id}>
                <b>{labels[provider.provider_type].slice(0, 1)}</b>
                <span><strong>{labels[provider.provider_type]}</strong><small>{provider.model_name || "Default model"} · {provider.connected ? "credential connected" : "disconnected"}</small></span>
                <span className={provider.active ? "tag green" : "tag"}>{provider.active ? "ACTIVE" : provider.connected ? "CONNECTED" : "DISCONNECTED"}</span>
                {provider.connected && !provider.active && <button className="btn" disabled={busy} onClick={() => void onUse(provider.id)}>Use</button>}
                {provider.connected && <button className="btn" disabled={busy} onClick={() => void onTest(provider.id)}>Test</button>}
                {provider.connected && <button className="btn" disabled={busy} onClick={() => startReplace(provider)}>Replace key</button>}
                {provider.connected && <button className="btn" disabled={busy} onClick={() => void onDisconnect(provider.id)}>Disconnect</button>}
                <button className="btn" disabled={busy} onClick={() => void onDelete(provider.id)}>Delete</button>
                {testState[provider.id] && <small>{testState[provider.id] === "testing" ? "Testing..." : testState[provider.id] === "ok" ? "Connection OK" : "Connection failed"}</small>}
              </div>
            ))}
            {status && <p className="upload-error">{status}</p>}
          </section>

          <section className="card">
            <h3>Privacy boundary</h3>
            <div className="grid3">
              <div><span className="iconbox">✓</span><h4>BYOK</h4><p>Your credential is entered through this UI, not hardcoded into the app.</p></div>
              <div><span className="iconbox">⌁</span><h4>Encrypted</h4><p>The backend stores encrypted credential material rather than plaintext keys.</p></div>
              <div><span className="iconbox">◈</span><h4>Knowledge-first</h4><p>Disconnecting AI does not delete documents, questions, practice data, or exports.</p></div>
            </div>
          </section>

          <section className="card">
            <h3>Workspace</h3>
            <p>Workspace and portability controls remain available below the AI boundary.</p>
            <button className="btn" onClick={async () => {
              try {
                const { data } = await apiClient.get("/ingestion/knowledge-bases");
                if (!data?.[0]?.id) return;
                const response = await apiClient.get("/portability/export", { params: { knowledge_base_id: data[0].id }, responseType: "blob" });
                const url = URL.createObjectURL(response.data);
                const a = document.createElement("a");
                a.href = url;
                a.download = "moduleiq-export.json";
                a.click();
                URL.revokeObjectURL(url);
              } catch (error) {
                setStatus(errorMessage(error));
              }
            }}>Export knowledge backup</button>
          </section>
        </div>
      </main>
    </div>
  );
}
