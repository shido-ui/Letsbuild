import { getLocalDocument, listLocalChunks, saveLocalSection, saveLocalTopic } from "./localDb";
import type { LocalSection, LocalTopic } from "./localDocumentTypes";

const headingPattern = /^(?:(chapter|unit|module|section)\s+)?(\d+(?:\.\d+)*)[.)\-:]?\s+(.{3,160})$/i;

function looksLikeHeading(text: string): string | null {
  const value = text.replace(/\s+/g, " ").trim();
  const match = value.match(headingPattern);
  if (match) return match[3].trim();
  if (value.length <= 100 && /^[A-Z][^.!?]{3,99}$/.test(value) && !/^[A-Z][a-z]+\s+(is|are|was|were)\b/.test(value)) return value;
  return null;
}

function keywords(text: string): string[] {
  const stop = new Set(["about","after","again","because","between","could","first","from","have","into","more","other","should","their","there","these","those","which","where","while","with","would","your"]);
  const counts = new Map<string, number>();
  for (const word of text.toLocaleLowerCase().split(/[^\p{L}\p{N}]+/u)) {
    if (word.length < 4 || stop.has(word)) continue;
    counts.set(word, (counts.get(word) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8).map(([word])=>word);
}

export async function buildLocalStructure(documentId: string): Promise<{sections: LocalSection[]; topics: LocalTopic[]}> {
  const document = await getLocalDocument(documentId);
  if (!document || document.status !== "ready") return { sections: [], topics: [] };
  const chunks = (await listLocalChunks()).filter((chunk) => chunk.documentId === documentId).sort((a,b)=>a.ordinal-b.ordinal);
  const sections: LocalSection[] = [];
  let current: LocalSection | null = null;

  for (const chunk of chunks) {
    const lines = chunk.text.split(/\n+/).map((line)=>line.trim()).filter(Boolean);
    const heading = lines.map(looksLikeHeading).find(Boolean);
    if (heading) {
      current = { id: crypto.randomUUID(), documentId, title: heading, level: 1, startPage: chunk.pageNumber, endPage: chunk.pageNumber, chunkIds: [chunk.id] };
      sections.push(current);
    } else if (current) {
      current.chunkIds.push(chunk.id);
      current.endPage = Math.max(current.endPage, chunk.pageNumber);
    } else {
      current = { id: crypto.randomUUID(), documentId, title: document.title, level: 1, startPage: chunk.pageNumber, endPage: chunk.pageNumber, chunkIds: [chunk.id] };
      sections.push(current);
    }
  }

  const topics: LocalTopic[] = [];
  for (const section of sections) {
    const sectionText = chunks.filter((chunk)=>section.chunkIds.includes(chunk.id)).map((chunk)=>chunk.text).join(" ");
    const topicWords = keywords(sectionText);
    for (const name of topicWords.slice(0, 6)) {
      topics.push({ id: crypto.randomUUID(), documentId, sectionId: section.id, name, keywords: topicWords, chunkIds: section.chunkIds.slice(0, 8) });
    }
    await saveLocalSection(section);
    for (const topic of topics.filter((item)=>item.sectionId===section.id)) await saveLocalTopic(topic);
  }
  return { sections, topics };
}
