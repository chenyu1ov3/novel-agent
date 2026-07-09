import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { describe, expect, it } from "vitest";

import {
  listProjectFiles,
  readNovelProject,
  rejectUnsafeProjectFile,
  toProjectFileTree,
} from "@/lib/novel-agent";

async function createFixtureProject() {
  const root = await mkdtemp(join(tmpdir(), "novel-agent-web-"));
  await mkdir(join(root, "bible"), { recursive: true });
  await mkdir(join(root, "chapters"), { recursive: true });
  await mkdir(join(root, "runs"), { recursive: true });
  await writeFile(
    join(root, "novel.yaml"),
    "title: 雪落长安\ngenre: 武侠悬疑\nlanguage: zh-CN\ntarget_words: 100000\n",
    "utf8",
  );
  await writeFile(join(root, "bible", "characters.md"), "# Characters\n\n沈青有一枚铜铃。", "utf8");
  await writeFile(join(root, "chapters", "ch001.md"), "# 第一章", "utf8");
  await writeFile(join(root, "runs", "ch001-demo.md"), "# Agent Trace", "utf8");
  return root;
}

describe("novel-agent project adapter", () => {
  it("reads project metadata and key files from a file-first novel project", async () => {
    const root = await createFixtureProject();
    try {
      const project = await readNovelProject(root);
      expect(project.config.title).toBe("雪落长安");
      expect(project.config.genre).toBe("武侠悬疑");
      expect(project.files.map((file) => file.path)).toContain("bible/characters.md");
      expect(project.files.map((file) => file.path)).toContain("runs/ch001-demo.md");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  it("builds a grouped file tree for bible, chapters, scenes, memory, and runs", async () => {
    const root = await createFixtureProject();
    try {
      const files = await listProjectFiles(root);
      const tree = toProjectFileTree(files);
      expect(tree.find((group) => group.name === "bible")?.files[0].path).toBe("bible/characters.md");
      expect(tree.find((group) => group.name === "runs")?.files[0].path).toBe("runs/ch001-demo.md");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  it("rejects unsafe file paths before reading or writing", () => {
    expect(() => rejectUnsafeProjectFile("../novel.yaml")).toThrow(/Unsafe project file/);
    expect(() => rejectUnsafeProjectFile("/tmp/novel.yaml")).toThrow(/Unsafe project file/);
    expect(() => rejectUnsafeProjectFile("bible/characters.md")).not.toThrow();
  });
});
