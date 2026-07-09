"use client";

import { DatabaseZap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNovelWorkspace } from "@/store/novel-workspace";

export function MemoryPanel() {
  const projectPath = useNovelWorkspace((state) => state.projectPath);
  const memoryBackend = useNovelWorkspace((state) => state.memoryBackend);
  const setMemoryBackend = useNovelWorkspace((state) => state.setMemoryBackend);

  async function index() {
    const response = await fetch("/api/memory/index", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ projectPath, backend: memoryBackend }),
    });
    const data = await response.json();
    window.alert(data.stdout || data.stderr || data.error || "Memory indexing complete");
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-3 flex items-center gap-2">
        <DatabaseZap className="h-4 w-4 text-primary" />
        <h3 className="font-medium">Vector memory</h3>
      </div>
      <div className="mb-3 grid grid-cols-2 gap-2 text-sm">
        {(["local", "pgvector"] as const).map((backend) => (
          <Button
            key={backend}
            variant={memoryBackend === backend ? "default" : "secondary"}
            size="sm"
            onClick={() => setMemoryBackend(backend)}
          >
            {backend}
          </Button>
        ))}
      </div>
      <Button className="w-full" variant="secondary" onClick={index} disabled={!projectPath}>
        Index memory
      </Button>
    </div>
  );
}
