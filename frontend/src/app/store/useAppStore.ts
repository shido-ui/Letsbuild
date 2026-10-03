import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AppUser = {
  id: string;
  username: string;
  email: string;
  is_active?: boolean;
};

type AppState = {
  token: string | null;
  user: AppUser | null;
  isAuthenticated: boolean;
  workspaceId: string | null;
  knowledgeBaseId: string | null;
  setSession: (token: string | null, user: AppUser | null) => void;
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
      isAuthenticated: false,
      workspaceId: null,
      knowledgeBaseId: null,
      setSession: (token, user) =>
        set({ token, user, isAuthenticated: Boolean(token) }),
      setWorkspaceId: (workspaceId) => set({ workspaceId }),
      setKnowledgeBaseId: (knowledgeBaseId) => set({ knowledgeBaseId }),
      logout: () =>
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          workspaceId: null,
          knowledgeBaseId: null,
        }),
      reset: () => set({ workspaceId: null, knowledgeBaseId: null }),
    }),
    { name: "moduleiq-app-state" },
  ),
);
