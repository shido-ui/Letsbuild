import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { apiClient, getApiBase, getRuntimeMode, setApiBase, setRuntimeMode, type RuntimeMode } from "../app/api/client";
import { AppChrome } from "../app/layout/AppChrome";
import { activateProvider, createProvider, deleteProvider, disconnectProvider, listProviders, testProvider, updateProvider } from "../app/api/providers";
import {
  activateStandaloneProvider,
  deleteStandaloneProvider,
  listStandaloneProviders,
  saveStandaloneProvider,
  testStandaloneProvider,
  type StandaloneProvider,
} from "../app/api/standaloneAI";
import type { Provider, ProviderType } from "../app/types/api";

const schema = z.object({
  provider_type: z.enum(["gemini", "openai", "openai_compatible", "local"]),
  model_name: z.string().trim().min(1).max(120),
  base_url: z.string().trim().url("Enter a valid URL").optional().or(z.literal("")),
  api_key: z.string().trim().min(1, "API key is required"),
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
  const [mode, setMode] = useState<RuntimeMode>(getRuntimeMode());
  const [providers, setProviders] = useState<Provider[]>([]);
  const [standaloneProviders, setStandaloneProviders] = useState<StandaloneProvider[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [testState, setTestState] = useState<Record<string, "testing" | "ok" | "error">>({});
  const [backendBase, setBackendBase] = useState(getApiBase());
  const [backendStatus, setBackendStatus] = useState("");
  const form = useForm<FormValues>({ defaultValues: defaults });
  const providerType = form.watch("provider_type");
  const selectedModel = form.watch("model_name");
  const active = useMemo(() => providers.find((p) => p.active), [providers]);
  const activeStandalone = useMemo(() => standaloneProviders.find((p) => p.active), [standaloneProviders]);

  async function refresh() {
    if (mode === "standalone") {
      setStandaloneProviders(await listStandaloneProviders());
      return;
    }
    try {
      setProviders(await listProviders());
    } catch (error) {
      setStatus(errorMessage(error));
    }
  }

  useEffect(() => { void refresh(); }, [mode]);

  useEffect(() => {
    const first = models[providerType][0];
    if (selectedModel && models[providerType].includes(selectedModel)) return;
    form.setValue("model_name", first);
    if (providerType === "openai") form.setValue("base_url", "https://api.openai.com/v1");
    else if (providerType === "gemini") form.setValue("base_url", "");
    if (providerType === "local") form.setValue("api_key", "local");
  }, [providerType]);

  function changeMode(next: RuntimeMode) {
    setRuntimeMode(next);
    setMode(next);
    setStatus(next === "standalone"
      ? "Standalone mode enabled. AI requests go directly from this app to the provider."
      : "Server mode enabled. AI requests use the configured ModuleIQ backend.");
  }

  async function onSubmit(raw: FormValues) {
    const parsed = schema.safeParse(raw);
    if (!parsed.success) {
      setStatus(parsed.error.issues[0]?.message || "Check the form.");
      return;
    }
    setBusy(true);
    setStatus("");
    try {
      if (mode === "standalone") {
        await saveStandaloneProvider(parsed.data);
        setStatus("Provider verified. The API key is stored locally in the encrypted app vault; it was not sent to ModuleIQ.");
        setStandaloneProviders(await listStandaloneProviders());
      } else if (editing) {
        await updateProvider(editing, parsed.data);
        setStatus("API key and provider settings updated and verified.");
        await refresh();
      } else {
        await createProvider(parsed.data);
        setStatus("Provider connected and verified.");
        await refresh();
      }
      form.reset(defaults);
      setEditing(null);
      setShowKey(false);
    } catch (error) {
      setStatus(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function onTest(id: string) {
    setTestState((s) => ({ ...s, [id]: "testing" }));
    try {
      if (mode === "standalone") await testStandaloneProvider(id);
      else await testProvider(id);
      setTestState((s) => ({ ...s, [id]: "ok" }));
    } catch {
      setTestState((s) => ({ ...s, [id]: "error" }));
    }
  }

  async function onUse(id: string) {
    setBusy(true);
    try {
      if (mode === "standalone") {
        await activateStandaloneProvider(id);
        setStandaloneProviders(await listStandaloneProviders());
      } else {
        await activateProvider(id);
        await refresh();
      }
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
      if (mode === "standalone") {
        await deleteStandaloneProvider(id);
        setStandaloneProviders(await listStandaloneProviders());
      } else {
        await disconnectProvider(id);
        await refresh();
      }
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
      if (mode === "standalone") {
        await deleteStandaloneProvider(id);
        setStandaloneProviders(await listStandaloneProviders());
      } else {
        await deleteProvider(id);
        await refresh();
      }
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

  async function testBackend() {
    setBackendStatus("Checking backend…");
    try {
      const base = setApiBase(backendBase);
      const root = base.endsWith("/api") ? base.slice(0, -4) : base;
      const response = await fetch(root + "/api");
      if (!response.ok) throw new Error("Backend returned an error.");
      setBackendStatus("Backend reachable.");
    } catch (error) {
      setBackendStatus(error instanceof Error ? error.message : "Backend unavailable.");
    }
  }

  return (
    <AppChrome title="Settings">
      <div className="title">
        <div>
          <h2>Settings</h2>
          <p>Runtime, AI connection, security, and workspace controls.</p>
        </div>
      </div>

      <div className="settings">
        <section className="card">
          <span className="tag purple">RUNTIME</span>
          <h2>How ModuleIQ runs</h2>
          <div className="grid3">
            <button className={mode === "standalone" ? "card active" : "card"} type="button" onClick={() => changeMode("standalone")}>
              <h3>Standalone APK</h3>
              <p>No ModuleIQ server for AI. The app calls your selected AI provider directly.</p>
              <span className="tag green">{mode === "standalone" ? "ACTIVE" : "SELECT"}</span>
            </button>
            <button className={mode === "server" ? "card active" : "card"} type="button" onClick={() => changeMode("server")}>
              <h3>ModuleIQ server</h3>
              <p>Use the existing FastAPI backend for server-managed AI credentials and workspace APIs.</p>
              <span className="tag">{mode === "server" ? "ACTIVE" : "SELECT"}</span>
            </button>
            <div>
              <h4>Plan A boundary</h4>
              <p>In standalone mode, your AI key never enters the ModuleIQ backend. Internet is still required for cloud AI.</p>
            </div>
          </div>
        </section>

        {mode === "standalone" ? (
          <>
            <section className="card">
              <span className="tag purple">AI ENGINE · STANDALONE</span>
              <h2>Connect your AI directly</h2>
              <p>Your key is tested directly against the provider, then encrypted locally. It is never posted to the ModuleIQ server.</p>
              <form onSubmit={form.handleSubmit(onSubmit)} className="settings-form">
                <label>Provider
                  <select {...form.register("provider_type")}>
                    {(Object.keys(labels) as ProviderType[]).map((type) => <option value={type} key={type}>{labels[type]}</option>)}
                  </select>
                </label>
                <label>Model
                  <select {...form.register("model_name")}>
                    {models[providerType].map((model) => <option value={model} key={model}>{model}</option>)}
                  </select>
                </label>
                {providerType === "openai_compatible" && <label>Base URL<input placeholder="https://your-provider.example/v1" {...form.register("base_url")} /></label>}
                {providerType === "openai" && <label>OpenAI endpoint<input {...form.register("base_url")} /></label>}
                {providerType !== "local" && (
                  <label>API key
                    <div className="key-field">
                      <input type={showKey ? "text" : "password"} autoComplete="off" placeholder="Paste your API key" {...form.register("api_key")} />
                      <button type="button" className="btn" onClick={() => setShowKey((v) => !v)}>{showKey ? "Hide" : "Show"}</button>
                    </div>
                  </label>
                )}
                {providerType === "local" && <p className="tag green">LOCAL MODEL · direct local endpoint</p>}
                <button className="btn primary" disabled={busy} type="submit">{busy ? "Testing & saving…" : "Test & connect directly"}</button>
              </form>
            </section>

            <section className="card">
              <h3>Standalone providers</h3>
              <p>{activeStandalone ? <>Active: <b>{labels[activeStandalone.provider_type]}</b> · {activeStandalone.model_name}</> : "No standalone provider is active."}</p>
              {standaloneProviders.map((provider) => (
                <div className="provider" key={provider.id}>
                  <b>{labels[provider.provider_type][0]}</b>
                  <span><strong>{labels[provider.provider_type]}</strong><small>{provider.model_name} · key {provider.key_fingerprint}</small></span>
                  <span className={provider.active ? "tag green" : "tag"}>{provider.active ? "ACTIVE" : "CONNECTED"}</span>
                  {!provider.active && <button className="btn" disabled={busy} onClick={() => void onUse(provider.id)}>Use</button>}
                  <button className="btn" disabled={busy} onClick={() => void onTest(provider.id)}>Test</button>
                  <button className="btn" disabled={busy} onClick={() => void onDelete(provider.id)}>Delete</button>
                  {testState[provider.id] && <small>{testState[provider.id] === "testing" ? "Testing..." : testState[provider.id] === "ok" ? "Connection OK" : "Connection failed"}</small>}
                </div>
              ))}
            </section>
          </>
        ) : (
          <>
            <section className="card">
              <span className="tag purple">RUNTIME</span>
              <h2>Backend connection</h2>
              <p>Choose the FastAPI server used by this web app or APK. AI keys stay on the backend.</p>
              <div className="settings-form">
                <label>API base URL<input value={backendBase} onChange={(event) => setBackendBase(event.target.value)} placeholder="http://127.0.0.1:8000/api" /></label>
                <div><button className="btn" type="button" onClick={() => void testBackend()}>Test connection</button><button className="btn primary" type="button" onClick={() => { setApiBase(backendBase); setBackendStatus("Backend URL saved."); }}>Save URL</button></div>
                {backendStatus && <small>{backendStatus}</small>}
              </div>
            </section>

            <section className="card">
              <span className="tag purple">AI ENGINE · SERVER</span>
              <h2>{editing ? "Replace API key" : "Connect an AI provider"}</h2>
              <p>Credentials are submitted to the configured FastAPI backend and encrypted at rest.</p>
              <form onSubmit={form.handleSubmit(onSubmit)} className="settings-form">
                <label>Provider<select {...form.register("provider_type")}>{(Object.keys(labels) as ProviderType[]).map((type) => <option value={type} key={type}>{labels[type]}</option>)}</select></label>
                <label>Model<select {...form.register("model_name")}>{models[providerType].map((model) => <option value={model} key={model}>{model}</option>)}</select></label>
                {providerType === "openai_compatible" && <label>Base URL<input placeholder="https://your-provider.example/v1" {...form.register("base_url")} /></label>}
                {providerType === "openai" && <label>OpenAI endpoint<input {...form.register("base_url")} /></label>}
                {providerType !== "local" && <label>API key<input type={showKey ? "text" : "password"} autoComplete="off" placeholder={editing ? "Enter replacement key" : "Paste your API key"} {...form.register("api_key")} /></label>}
                <div><button className="btn primary" disabled={busy} type="submit">{busy ? "Saving..." : editing ? "Replace & verify" : "Test & connect"}</button></div>
              </form>
            </section>

            <section className="card">
              <h3>Connected providers</h3>
              <p>{active ? <>Active: <b>{labels[active.provider_type]}</b></> : "No provider is currently active."}</p>
              {providers.map((provider) => (
                <div className="provider" key={provider.id}>
                  <b>{labels[provider.provider_type][0]}</b>
                  <span><strong>{labels[provider.provider_type]}</strong><small>{provider.model_name || "Default model"} · {provider.connected ? "credential connected" : "disconnected"}</small></span>
                  <span className={provider.active ? "tag green" : "tag"}>{provider.active ? "ACTIVE" : provider.connected ? "CONNECTED" : "DISCONNECTED"}</span>
                  {provider.connected && !provider.active && <button className="btn" disabled={busy} onClick={() => void onUse(provider.id)}>Use</button>}
                  {provider.connected && <button className="btn" disabled={busy} onClick={() => void onTest(provider.id)}>Test</button>}
                  {provider.connected && <button className="btn" disabled={busy} onClick={() => void onDisconnect(provider.id)}>Disconnect</button>}
                  <button className="btn" disabled={busy} onClick={() => void onDelete(provider.id)}>Delete</button>
                </div>
              ))}
            </section>
          </>
        )}

        <section className="card">
          <h3>Privacy boundary</h3>
          <div className="grid3">
            <div><span className="iconbox">✓</span><h4>BYOK</h4><p>Your credential is entered through Settings, not hardcoded into the app.</p></div>
            <div><span className="iconbox">⌁</span><h4>Local vault</h4><p>Standalone credentials are encrypted with a non-exportable Web Crypto key stored inside the app vault.</p></div>
            <div><span className="iconbox">◈</span><h4>Knowledge-first</h4><p>Changing or disconnecting AI does not delete your knowledge.</p></div>
          </div>
        </section>

        {mode === "server" && <section className="card"><h3>Workspace</h3><p>Server-mode portability controls remain available here.</p><button className="btn" onClick={async () => {
          try {
            const { data } = await apiClient.get("/ingestion/knowledge-bases");
            if (!data?.[0]?.id) return;
            const response = await apiClient.get("/portability/export", { params: { knowledge_base_id: data[0].id }, responseType: "blob" });
            const url = URL.createObjectURL(response.data);
            const a = document.createElement("a"); a.href = url; a.download = "moduleiq-export.json"; a.click(); URL.revokeObjectURL(url);
          } catch (error) { setStatus(errorMessage(error)); }
        }}>Export knowledge backup</button></section>}

        {status && <p className="upload-error">{status}</p>}
      </div>
    </AppChrome>
  );
}
