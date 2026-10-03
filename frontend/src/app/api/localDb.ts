import type { RuntimeMode } from "./client";
import type { LocalChunk, LocalDocument } from "./localDocumentTypes";

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
    blob?: Blob;
  }>;
  counts: Record<string, number>;
};

const DB_NAME = "moduleiq-local";
const STORE = "state";
const KEY = "knowledge-base";
const DOC_PREFIX = "document:";
const CHUNK_PREFIX = "chunk:";

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

export async function getLocalKnowledgeBase(): Promise<LocalKnowledgeBase | null> {
  return read<LocalKnowledgeBase>(KEY);
}

export async function ensureLocalKnowledgeBase(): Promise<LocalKnowledgeBase> {
  const existing = await getLocalKnowledgeBase();
  if (existing) return existing;
  const created: LocalKnowledgeBase = {
    id: crypto.randomUUID(), workspaceId: crypto.randomUUID(), name: "My Knowledge Base",
    description: "Your private on-device learning workspace.", createdAt: new Date().toISOString(),
    materials: [], counts: { documents: 0, questions: 0, topics: 0, solutions: 0, pages: 0, equations: 0 },
  };
  await write(KEY, created);
  return created;
}

export function saveLocalKnowledgeBase(value: LocalKnowledgeBase): Promise<void> { return write(KEY, value); }

export function getLocalDocument(documentId: string): Promise<LocalDocument | null> {
  return read<LocalDocument>(DOC_PREFIX + documentId);
}

export function saveLocalDocument(document: LocalDocument): Promise<void> {
  return write(DOC_PREFIX + document.id, document);
}

export function getLocalChunk(chunkId: string): Promise<LocalChunk | null> {
  return read<LocalChunk>(CHUNK_PREFIX + chunkId);
}

export function saveLocalChunk(chunk: LocalChunk): Promise<void> {
  return write(CHUNK_PREFIX + chunk.id, chunk);
}

export async function listLocalChunks(): Promise<LocalChunk[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const chunks: LocalChunk[] = [];
    const request = db.transaction(STORE, "readonly").objectStore(STORE).openCursor();
    request.onsuccess = () => {
      const cursor = request.result;
      if (!cursor) { resolve(chunks); return; }
      if (typeof cursor.key === "string" && cursor.key.startsWith(CHUNK_PREFIX)) chunks.push(cursor.value as LocalChunk);
      cursor.continue();
    };
    request.onerror = () => reject(request.error);
  });
}

export async function addLocalMaterial(file: File, knowledgeBaseId: string): Promise<LocalKnowledgeBase> {
  const current = await ensureLocalKnowledgeBase();
  if (current.id !== knowledgeBaseId) throw new Error("Knowledge base changed. Reload and try again.");
  const duplicate = current.materials.find((m) => m.name === file.name && m.size_bytes === file.size);
  if (duplicate) return current;
  const materialId = crypto.randomUUID();
  const documentId = crypto.randomUUID();
  const next: LocalKnowledgeBase = {
    ...current,
    materials: [...current.materials, {
      id: materialId, name: file.name, media_type: file.type || "application/octet-stream",
      size_bytes: file.size, documents: [{ id: documentId, title: file.name, status: "stored-local" }], blob: file,
    }],
    counts: { ...current.counts, documents: current.counts.documents + 1 },
  };
  await saveLocalKnowledgeBase(next);
  return next;
}

export async function listLocalDocuments(): Promise<LocalDocument[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const documents: LocalDocument[] = [];
    const request = db.transaction(STORE, "readonly").objectStore(STORE).openCursor();
    request.onsuccess = () => {
      const cursor = request.result;
      if (!cursor) { resolve(documents); return; }
      if (typeof cursor.key === "string" && cursor.key.startsWith(DOC_PREFIX)) {
        documents.push(cursor.value as LocalDocument);
      }
      cursor.continue();
    };
    request.onerror = () => reject(request.error);
  });
}

export async function clearLocalKnowledgeBase(): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    store.delete(KEY);
    const cursorRequest = store.openCursor();
    cursorRequest.onsuccess = () => {
      const cursor = cursorRequest.result;
      if (!cursor) return;
      if (typeof cursor.key === "string" && (cursor.key.startsWith(DOC_PREFIX) || cursor.key.startsWith(CHUNK_PREFIX))) cursor.delete();
      cursor.continue();
    };
    cursorRequest.onerror = () => reject(cursorRequest.error);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export function isStandaloneRuntime(mode: RuntimeMode) { return mode === "standalone"; }
