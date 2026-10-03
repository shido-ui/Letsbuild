import { getLocalDocument, listLocalDocuments, saveLocalChunk } from "./localDb";
import type { LocalChunk } from "./localDocumentTypes";

const TARGET_CHARS = 2400;
const OVERLAP_CHARS = 280;

function estimateTokens(text: string): number {
  return Math.max(1, Math.ceil(text.length / 4));
}

async function makeChunks(documentId: string, pageNumber: number, text: string, startOrdinal: number): Promise<LocalChunk[]> {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) return [];
  const chunks: LocalChunk[] = [];
  let start = 0;
  let ordinal = startOrdinal;
  while (start < normalized.length) {
    let end = Math.min(normalized.length, start + TARGET_CHARS);
    if (end < normalized.length) {
      const boundary = normalized.lastIndexOf(" ", end);
      if (boundary > start + TARGET_CHARS * 0.65) end = boundary;
    }
    const value = normalized.slice(start, end).trim();
    if (value) chunks.push({
      id: documentId + ":" + ordinal,
      documentId, pageNumber, ordinal, text: value,
      characterCount: value.length, tokenEstimate: estimateTokens(value),
    });
    if (end >= normalized.length) break;
    start = Math.max(start + 1, end - OVERLAP_CHARS);
    ordinal += 1;
  }
  for (const chunk of chunks) await saveLocalChunk(chunk);
  return chunks;
}

export async function buildLocalChunks(documentId: string): Promise<LocalChunk[]> {
  const document = await getLocalDocument(documentId);
  if (!document || document.status !== "ready") return [];
  const chunks: LocalChunk[] = [];
  let ordinal = 0;
  for (const page of document.pages) {
    const pageChunks = await makeChunks(document.id, page.pageNumber, page.text, ordinal);
    chunks.push(...pageChunks);
    ordinal += pageChunks.length;
  }
  return chunks;
}

export async function buildAllLocalChunks(): Promise<LocalChunk[]> {
  const documents = await listLocalDocuments();
  const all: LocalChunk[] = [];
  for (const document of documents) {
    if (document.status === "ready") all.push(...await buildLocalChunks(document.id));
  }
  return all;
}
