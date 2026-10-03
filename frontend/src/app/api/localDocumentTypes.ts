export type LocalPage = {
  pageNumber: number;
  text: string;
  characterCount: number;
};

export type LocalDocument = {
  id: string;
  materialId: string;
  title: string;
  mediaType: string;
  sizeBytes: number;
  sha256: string;
  status: "processing" | "ready" | "failed";
  createdAt: string;
  processedAt?: string;
  pageCount: number;
  characterCount: number;
  text: string;
  pages: LocalPage[];
  error?: string;
};

export type LocalChunk = {
  id: string;
  documentId: string;
  pageNumber: number;
  ordinal: number;
  text: string;
  characterCount: number;
  tokenEstimate: number;
};

export type LocalSection = {
  id: string;
  documentId: string;
  title: string;
  level: number;
  startPage: number;
  endPage: number;
  chunkIds: string[];
  summary?: string;
};

export type LocalTopic = {
  id: string;
  documentId: string;
  sectionId: string;
  name: string;
  keywords: string[];
  chunkIds: string[];
};
