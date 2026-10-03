import type { RuntimeMode } from "./client";

export type LocalKnowledgeBase = {
  id: string;
  workspaceId: string;
  name: string;
  description: string;
  createdAt: string;
  materials: Array<{
    id: string;
    name: string;
    media_type: string;
    size_bytes: number;
    sha256?: string;
    documents: Array<{ id: string; title: string; status: string }>;
  }>;
  counts: Record<string, number>;
};

const DB_NAME = "moduleiq-local";
const STORE = "state";
const KEY = "knowledge-base";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function read<T>(key: string): Promise<T | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const req = db.transaction(STORE, "readonly").objectStore(STORE).get(key);
    req.onsuccess = () => resolve((req.result as T | undefined) ?? null);
    req.onerror = () => reject(req.error);
  });
}

async function write<T>(key: string, value: T): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(value, key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getLocalKnowledgeBase() { return read<LocalKnowledgeBase>(KEY); }

export async function ensureLocalKnowledgeBase(): Promise<LocalKnowledgeBase> {
  const existing = await getLocalKnowledgeBase();
  if (existing) return existing;
  const now = new Date().toISOString();
  const created: LocalKnowledgeBase = {
    id: crypto.randomUUID(), workspaceId: crypto.randomUUID(),
    name: "My Knowledge Base",
    description: "Your private on-device learning workspace.",
    createdAt: now, materials: [],
    counts: { documents: 0, questions: 0, topics: 0, solutions: 0, pages: 0, equations: 0 },
  };
  await write(KEY, created);
  return created;
}

export async function saveLocalKnowledgeBase(value: LocalKnowledgeBase) { return write(KEY, value); }

export async function clearLocalKnowledgeBase(): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(KEY);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export function isStandaloneRuntime(mode: RuntimeMode) { return mode === "standalone"; }
