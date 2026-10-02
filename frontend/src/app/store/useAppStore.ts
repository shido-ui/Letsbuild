import { create } from "zustand";
import { persist } from "zustand/middleware";

type AppState = {
  workspaceId: string | null;
  knowledgeBaseId: string | null;
  setWorkspaceId: (id: string | null) => void;
  setKnowledgeBaseId: (id: string | null) => void;
  reset: () => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      workspaceId: null,
      knowledgeBaseId: null,
      setWorkspaceId: (workspaceId) => set({ workspaceId }),
      setKnowledgeBaseId: (knowledgeBaseId) => set({ knowledgeBaseId }),
      reset: () => set({ workspaceId: null, knowledgeBaseId: null }),
    }),
    { name: "moduleiq-app-state" },
  ),
);
