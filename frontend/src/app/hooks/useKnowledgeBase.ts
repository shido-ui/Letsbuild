import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { useAppStore } from "../store/useAppStore";

export function useKnowledgeBase() {
  const id = useAppStore((s) => s.knowledgeBaseId);
  const setId = useAppStore((s) => s.setKnowledgeBaseId);
  const [knowledgeBase, setKnowledgeBase] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await apiClient.get("/ingestion/knowledge-bases");
        const selected = list.data.find((x: any) => x.id === id) || list.data[0];
        if (!selected) throw new Error("No knowledge base exists yet. Upload material to create one.");
        if (!id) setId(selected.id);
        const response = await apiClient.get(`/knowledge-bases/${selected.id}`);
        if (!cancelled) setKnowledgeBase(response.data);
      } catch (e: any) {
        if (!cancelled) setError(e.response?.data?.detail || e.message || "Failed to load knowledge base.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [id, setId]);

  return { id: knowledgeBase?.id || id, knowledgeBase, loading, error, refresh: async () => {
    if (knowledgeBase?.id) {
      const response = await apiClient.get(`/knowledge-bases/${knowledgeBase.id}`);
      setKnowledgeBase(response.data);
    }
  }};
}
