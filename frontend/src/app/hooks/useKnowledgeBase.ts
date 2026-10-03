import { useCallback, useEffect, useState } from "react";
import { apiClient, getRuntimeMode } from "../api/client";
import { ensureLocalKnowledgeBase, getLocalKnowledgeBase } from "../api/localDb";
import { useAppStore } from "../store/useAppStore";

export function useKnowledgeBase() {
  const id = useAppStore((s) => s.knowledgeBaseId);
  const setId = useAppStore((s) => s.setKnowledgeBaseId);
  const [knowledgeBase, setKnowledgeBase] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      if (getRuntimeMode() === "standalone") {
        const local = await ensureLocalKnowledgeBase();
        if (!id) setId(local.id);
        setKnowledgeBase(local);
        return;
      }
      const list = await apiClient.get("/ingestion/knowledge-bases");
      const selected = list.data.find((x: any) => x.id === id) || list.data[0];
      if (!selected) throw new Error("No knowledge base exists yet. Upload material to create one.");
      if (!id) setId(selected.id);
      const response = await apiClient.get(`/knowledge-bases/${selected.id}`);
      setKnowledgeBase(response.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || "Failed to load knowledge base.");
    } finally {
      setLoading(false);
    }
  }, [id, setId]);

  useEffect(() => { load().catch(() => undefined); }, [load]);

  return {
    id: knowledgeBase?.id || id,
    knowledgeBase,
    loading,
    error,
    refresh: async () => {
      if (getRuntimeMode() === "standalone") {
        const local = await getLocalKnowledgeBase();
        if (local) setKnowledgeBase(local);
        return;
      }
      if (knowledgeBase?.id) {
        const response = await apiClient.get(`/knowledge-bases/${knowledgeBase.id}`);
        setKnowledgeBase(response.data);
      }
    },
  };
}
