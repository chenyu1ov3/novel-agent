"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useNovelWorkspace } from "@/store/novel-workspace";

export function AssetEditor() {
  const projectPath = useNovelWorkspace((state) => state.projectPath);
  const selectedFile = useNovelWorkspace((state) => state.selectedFile);
  const [content, setContent] = useState("");
  const [status, setStatus] = useState("Select a project file to edit Markdown/YAML assets.");

  useEffect(() => {
    if (!projectPath || !selectedFile) return;
    setStatus("Loading file…");
    fetch(`/api/file?projectPath=${encodeURIComponent(projectPath)}&filePath=${encodeURIComponent(selectedFile)}`)
      .then((response) => response.json())
      .then((data: { content?: string; error?: string }) => {
        setContent(data.content || "");
        setStatus(data.error || `Editing ${selectedFile}`);
      })
      .catch((error: Error) => setStatus(error.message));
  }, [projectPath, selectedFile]);

  async function save() {
    if (!projectPath || !selectedFile) return;
    setStatus("Saving…");
    const response = await fetch("/api/file", {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ projectPath, filePath: selectedFile, content }),
    });
    const data = (await response.json()) as { error?: string };
    setStatus(response.ok ? `Saved ${selectedFile}` : data.error || "Save failed");
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-[-0.02em]">Asset editor</h2>
          <p className="text-sm text-muted-foreground">{status}</p>
        </div>
        <Button size="sm" variant="secondary" onClick={save} disabled={!selectedFile}>
          <Save className="mr-2 h-4 w-4" /> Save
        </Button>
      </div>
      <Textarea
        className="min-h-[28rem] font-mono text-sm leading-6"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="# Markdown project asset"
      />
    </div>
  );
}
