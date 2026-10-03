import { listLocalChunks } from "./localDb";
import type { LocalChunk } from "./localDocumentTypes";

export type LocalRetrieval = LocalChunk & { score: number };

function terms(value: string): string[] {
  return value.toLocaleLowerCase().split(/[^\p{L}\p{N}]+/u).filter((term) => term.length >= 2);
}

export async function retrieveLocalChunks(query: string, limit = 8): Promise<LocalRetrieval[]> {
  const queryTerms = terms(query);
  if (!queryTerms.length) return [];
  const chunks = await listLocalChunks();
  return chunks.map((chunk) => {
    const haystack = chunk.text.toLocaleLowerCase();
    const score = queryTerms.reduce((total, term) => {
      let count = 0;
      let offset = 0;
      while ((offset = haystack.indexOf(term, offset)) >= 0) {
        count += 1;
        offset += term.length;
      }
      return total + count;
    }, 0);
  }).filter((item) => item.score > 0).sort((a, b) => b.score - a.score).slice(0, limit);
}
