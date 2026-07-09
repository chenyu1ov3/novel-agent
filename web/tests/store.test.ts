import { describe, expect, it } from "vitest";

import { createNovelWorkspaceStore } from "@/store/novel-workspace";

describe("novel workspace Zustand store", () => {
  it("tracks selected project, selected file, and run drafts", () => {
    const store = createNovelWorkspaceStore();
    store.getState().setProjectPath("/tmp/book");
    store.getState().selectFile("bible/characters.md");
    store.getState().setDraftGoal("发现铜铃");

    expect(store.getState().projectPath).toBe("/tmp/book");
    expect(store.getState().selectedFile).toBe("bible/characters.md");
    expect(store.getState().draftGoal).toBe("发现铜铃");
  });
});
