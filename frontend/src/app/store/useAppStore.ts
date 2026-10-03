import { create } from "zustand";
import { persist } from "zustand/middleware";
import { setApiToken } from "../api/client";

export type AuthUser = {
  id: string;
  username: string;
  email: string;
  display_name?: string | null;
  is_active: boolean;
};

type AppState = {
  token: string | null;
  user: AuthUser | null;
  workspaceId: string | null;
  knowledgeBaseId: string | null;
  setToken: (token: string | null) => void;
  setUser: (user: AuthUser | null) => void;
  setWorkspaceId: (id: string | null) => void;
  setKnowledgeBaseId: (id: string | null) => void;
  logout: () => void;
  reset: () => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      workspaceId: null,
      knowledgeBaseId: null,
      setToken: (token) => {
        setApiToken(token);
        set({ token });
      },
      setUser: (user) => set({ user }),
      setWorkspaceId: (workspaceId) => set({ workspaceId }),
      setKnowledgeBaseId: (knowledgeBaseId) => set({ knowledgeBaseId }),
      logout: () => {
        setApiToken(null);
        set({ token: null, user: null });
      },
      reset: () => set({ workspaceId: null, knowledgeBaseId: null }),
    }),
    {
      name: "moduleiq-app-state",
      onRehydrateStorage: () => (state) => setApiToken(state?.token ?? null),
    },
  ),
);
