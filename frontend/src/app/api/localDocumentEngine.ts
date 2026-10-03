import * as pdfjs from "pdfjs-dist/legacy/build/pdf.mjs";
import mammoth from "mammoth";
import { getLocalDocument, getLocalKnowledgeBase, saveLocalDocument, saveLocalKnowledgeBase } from "./localDb";
import type { LocalDocument } from "./localDocumentTypes";

async function hashFile(file: Blob): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function splitDocxText(text: string) {
  const paragraphs = text.split(/\n{2,}/).map((value) => value.trim()).filter(Boolean);
  if (!paragraphs.length) return text.trim() ? [{ pageNumber: 1, text: text.trim(), characterCount: text.trim().length }] : [];
  return paragraphs.map((value, index) => ({ pageNumber: index + 1, text: value, characterCount: value.length }));
}

async function extractPdf(file: Blob) {
  const pdf = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
  const pages = [];
  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const content = await page.getTextContent();
    const text = content.items.map((item) => ("str" in item ? item.str : "")).join(" ").replace(/[ \t]+/g, " ").trim();
    pages.push({ pageNumber, text, characterCount: text.length });
  }
  return pages;
}

async function extractDocx(file: Blob) {
  const result = await mammoth.extractRawText({ arrayBuffer: await file.arrayBuffer() });
  return splitDocxText(result.value.trim());
}

export async function processLocalDocument(materialId: string, documentId: string): Promise<LocalDocument> {
  const kb = await getLocalKnowledgeBase();
  if (!kb) throw new Error("Local knowledge base is unavailable.");
  const material = kb.materials.find((item) => item.id === materialId);
  if (!material?.blob) throw new Error("Local material file is unavailable.");

  const existing = await getLocalDocument(documentId);
  const started: LocalDocument = {
    id: documentId, materialId, title: material.name, mediaType: material.media_type,
    sizeBytes: material.size_bytes, sha256: existing?.sha256 ?? "", status: "processing",
    createdAt: existing?.createdAt ?? new Date().toISOString(), pageCount: 0, characterCount: 0, text: "", pages: [],
  };
  await saveLocalDocument(started);
  await updateMaterialStatus(kb, materialId, documentId, "processing");

  try {
    const sha256 = await hashFile(material.blob);
    const pages = material.media_type === "application/pdf" ? await extractPdf(material.blob) : await extractDocx(material.blob);
    const text = pages.map((page) => page.text).filter(Boolean).join("\n\n").trim();
    const ready: LocalDocument = {
      ...started, sha256, status: "ready", processedAt: new Date().toISOString(),
      pageCount: pages.length, characterCount: text.length, text, pages,
    };
    await saveLocalDocument(ready);
    await updateMaterialStatus(kb, materialId, documentId, "ready", sha256, pages.length);
    return ready;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Document extraction failed.";
    const failed = { ...started, status: "failed" as const, error: message };
    await saveLocalDocument(failed);
    await updateMaterialStatus(kb, materialId, documentId, "failed");
    return failed;
  }
}

async function updateMaterialStatus(
  kb: NonNullable<Awaited<ReturnType<typeof getLocalKnowledgeBase>>>,
  materialId: string,
  documentId: string,
  status: string,
  sha256?: string,
  pageCount?: number,
) {
  const material = kb.materials.find((item) => item.id === materialId);
  const previousStatus = material?.documents.find((doc) => doc.id === documentId)?.status;
  const nextCounts = { ...kb.counts };
  if (previousStatus !== "ready" && status === "ready") nextCounts.pages = (nextCounts.pages ?? 0) + (pageCount ?? 0);
  await saveLocalKnowledgeBase({
    ...kb,
    materials: kb.materials.map((item) => item.id !== materialId ? item : {
      ...item, sha256: sha256 ?? item.sha256,
      documents: item.documents.map((doc) => doc.id === documentId ? { ...doc, status } : doc),
    }),
    counts: nextCounts,
  });
}

export async function processAllLocalDocuments(): Promise<LocalDocument[]> {
  const kb = await getLocalKnowledgeBase();
  if (!kb) return [];
  const results: LocalDocument[] = [];
  for (const material of kb.materials) {
    for (const document of material.documents) {
      results.push(await processLocalDocument(material.id, document.id));
    }
  }
  return results;
}
