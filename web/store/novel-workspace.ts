import { create, type StoreApi, type UseBoundStore } from "zustand";

export type NovelWorkspaceState = {
  projectPath: string;
  selectedFile: string | null;
  draftChapter: number;
  draftGoal: string;
  memoryBackend: "local" | "pgvector";
  setProjectPath: (projectPath: string) => void;
  selectFile: (selectedFile: string | null) => void;
  setDraftChapter: (draftChapter: number) => void;
  setDraftGoal: (draftGoal: string) => void;
  setMemoryBackend: (memoryBackend: "local" | "pgvector") => void;
};

export function createNovelWorkspaceStore(): UseBoundStore<StoreApi<NovelWorkspaceState>> {
  return create<NovelWorkspaceState>()((set) => ({
    projectPath: "",
    selectedFile: null,
    draftChapter: 1,
    draftGoal: "按章节大纲推进剧情",
    memoryBackend: "local",
    setProjectPath: (projectPath) => set({ projectPath }),
    selectFile: (selectedFile) => set({ selectedFile }),
    setDraftChapter: (draftChapter) => set({ draftChapter }),
    setDraftGoal: (draftGoal) => set({ draftGoal }),
    setMemoryBackend: (memoryBackend) => set({ memoryBackend }),
  }));
}

export const useNovelWorkspace = createNovelWorkspaceStore();
