import { listLocalDocuments } from "./localDb";

export type LocalSearchResult = {
  kind: "document";
  object_id: string;
  title: string;
  content: string;
  snippet: string;
  source_document_id: string;
  score: number;
};

function terms(value: string): string[] {
  return value.toLocaleLowerCase().split(/[^\p{L}\p{N}]+/u).filter((term) => term.length >= 2);
}

function snippet(text: string, query: string): string {
  const normalized = text.replace(/\s+/g, " ").trim();
  const index = normalized.toLocaleLowerCase().indexOf(query.toLocaleLowerCase());
  if (index < 0) return normalized.slice(0, 240);
  const start = Math.max(0, index - 80);
  return (start ? "… " : "") + normalized.slice(start, start + 260) + (start + 260 < normalized.length ? " …" : "");
}

export async function searchLocalDocuments(query: string, limit = 50): Promise<LocalSearchResult[]> {
  const queryTerms = terms(query);
  if (!queryTerms.length) return [];
  const documents = await listLocalDocuments();
  return documents
    .filter((document) => document.status === "ready")
    .map((document) => {
      const haystack = document.text.toLocaleLowerCase();
      const score = queryTerms.reduce((total, term) => {
        let count = 0;
        let cursor = 0;
        while ((cursor = haystack.indexOf(term, cursor)) >= 0) { count += 1; cursor += term.length; }
        return total + count;
      }, 0);
      return {
        kind: "document" as const, object_id: document.id, title: document.title,
        content: document.text, snippet: snippet(document.text, query),
        source_document_id: document.id, score,
      };
    })
    .filter((result) => result.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
