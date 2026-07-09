"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { Bot, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useNovelWorkspace } from "@/store/novel-workspace";

export function AgentRunner() {
  const projectPath = useNovelWorkspace((state) => state.projectPath);
  const draftChapter = useNovelWorkspace((state) => state.draftChapter);
  const draftGoal = useNovelWorkspace((state) => state.draftGoal);
  const setDraftChapter = useNovelWorkspace((state) => state.setDraftChapter);
  const setDraftGoal = useNovelWorkspace((state) => state.setDraftGoal);
  const [events, setEvents] = useState<string[]>([]);
  const chat = useChat({ api: "/api/agent/run" });

  async function run() {
    setEvents(["Starting run…"]);
    const response = await fetch("/api/agent/run", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ projectPath, chapter: draftChapter, goal: draftGoal }),
    });
    const text = await response.text();
    setEvents((current) => [...current, text]);
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-3 flex items-center gap-2">
        <Bot className="h-4 w-4 text-primary" />
        <h3 className="font-medium">Multi-agent run</h3>
      </div>
      <div className="grid gap-3">
        <Input
          type="number"
          min={1}
          value={draftChapter}
          onChange={(event) => setDraftChapter(Number(event.target.value))}
        />
        <Textarea value={draftGoal} onChange={(event) => setDraftGoal(event.target.value)} />
        <Button onClick={run} disabled={!projectPath || chat.isLoading}>
          <Play className="mr-2 h-4 w-4" /> Run agent pipeline
        </Button>
      </div>
      <pre className="mt-4 max-h-64 overflow-auto rounded-lg bg-black/30 p-3 font-mono text-xs text-muted-foreground">
        {events.join("\n\n") || "Agent stream and command results will appear here."}
      </pre>
    </div>
  );
}
