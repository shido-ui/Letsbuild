import { listLocalChunks, listLocalQuestions, saveLocalQuestion } from "./localDb";
import type { LocalChunk } from "./localDocumentTypes";
import type { LocalQuestion } from "./localDb";

function sentence(text: string): string {
  return text.split(/(?<=[.!?])\s+/).map((value)=>value.trim()).find((value)=>value.length >= 45 && value.length <= 280) ?? text.slice(0, 240).trim();
}

function makeQuestion(chunk: LocalChunk, sourceTitle: string, ordinal: number): LocalQuestion | null {
  const source = sentence(chunk.text);
  if (source.length < 25) return null;
  const words = source.split(/\s+/).filter((word)=>word.length > 5);
  const answer = words.slice(0, 18).join(" ");
  if (!answer) return null;
  const masked = source.replace(answer, "_____");
  return {
    id: chunk.documentId + ":q:" + ordinal,
    documentId: chunk.documentId,
    chunkId: chunk.id,
    prompt: "Complete the missing part from the source: " + masked,
    answer,
    type: "short_answer",
    difficulty: answer.length > 70 ? "medium" : "easy",
    sourcePage: chunk.pageNumber,
    sourceTitle,
    createdAt: new Date().toISOString(),
  };
}

export async function generateLocalQuestions(chunks: LocalChunk[], sourceTitle: string, maxQuestions = 20): Promise<LocalQuestion[]> {
  const existing = await listLocalQuestions();
  const generated: LocalQuestion[] = [];
  for (const chunk of chunks.slice(0, maxQuestions * 2)) {
    if (existing.some((question)=>question.chunkId===chunk.id)) continue;
    const question = makeQuestion(chunk, sourceTitle, generated.length);
    if (!question) continue;
    await saveLocalQuestion(question);
    generated.push(question);
    if (generated.length >= maxQuestions) break;
  }
  return generated;
}
