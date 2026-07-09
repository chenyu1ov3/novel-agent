"use client";

import { FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNovelWorkspace } from "@/store/novel-workspace";

export function ProjectLoader({ onLoad }: { onLoad: (projectPath: string) => void }) {
  const projectPath = useNovelWorkspace((state) => state.projectPath);
  const setProjectPath = useNovelWorkspace((state) => state.setProjectPath);

  return (
    <form
      className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-4 md:flex-row"
      onSubmit={(event) => {
        event.preventDefault();
        if (projectPath.trim()) onLoad(projectPath.trim());
      }}
    >
      <div className="flex flex-1 items-center gap-3">
        <FolderOpen className="h-5 w-5 text-muted-foreground" />
        <Input
          aria-label="Novel project path"
          value={projectPath}
          onChange={(event) => setProjectPath(event.target.value)}
          placeholder="/path/to/my-novel"
        />
      </div>
      <Button type="submit">Open project</Button>
    </form>
  );
}
