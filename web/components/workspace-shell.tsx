"use client";

import { useState } from "react";
import { Activity, BookOpen, GitBranch, PenLine } from "lucide-react";
import type { NovelProject } from "@/lib/novel-agent";
import { AssetEditor } from "@/components/asset-editor";
import { AgentRunner } from "@/components/agent-runner";
import { FileTree } from "@/components/file-tree";
import { MemoryPanel } from "@/components/memory-panel";
import { ProjectLoader } from "@/components/project-loader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useNovelWorkspace } from "@/store/novel-workspace";

export function WorkspaceShell() {
  const setProjectPath = useNovelWorkspace((state) => state.setProjectPath);
  const [project, setProject] = useState<NovelProject | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load(projectPath: string) {
    setProjectPath(projectPath);
    setError(null);
    const response = await fetch(`/api/project?path=${encodeURIComponent(projectPath)}`);
    const data = (await response.json()) as NovelProject | { error: string };
    if (!response.ok || "error" in data) {
      setError("error" in data ? data.error : "Failed to load project");
      return;
    }
    setProject(data);
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-5 py-8">
      <section className="space-y-6 py-6">
        <div className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 font-mono text-xs text-muted-foreground">
          novel-agent web · multi-agent workspace
        </div>
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
          <div>
            <h1 className="max-w-4xl text-5xl font-medium leading-none tracking-[-0.06em] md:text-7xl">
              Browser cockpit for long-form fiction agents.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
              Open a Markdown/YAML novel project, index vector memory, inspect agent traces, and run the story architect → continuity guardian → writer → editor → critic pipeline.
            </p>
          </div>
          <ProjectLoader onLoad={load} />
        </div>
        {error ? <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</div> : null}
      </section>

      {project ? <ProjectWorkspace project={project} /> : <EmptyState />}
    </main>
  );
}

function ProjectWorkspace({ project }: { project: NovelProject }) {
  return (
    <div className="grid gap-6 lg:grid-cols-[18rem_1fr_22rem]">
      <aside className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-primary" /> {project.config.title}
            </CardTitle>
            <p className="text-sm text-muted-foreground">{project.config.genre} · {project.config.language}</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
              <Metric label="Files" value={project.files.length.toString()} />
              <Metric label="Target" value={project.config.targetWords ? `${Math.round(project.config.targetWords / 1000)}k` : "—"} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Project files</CardTitle>
          </CardHeader>
          <CardContent>
            <FileTree groups={project.groups} />
          </CardContent>
        </Card>
      </aside>

      <Card>
        <CardContent className="pt-5">
          <AssetEditor />
        </CardContent>
      </Card>

      <aside className="space-y-4">
        <MemoryPanel />
        <AgentRunner />
      </aside>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {[
        [GitBranch, "File-first", "Keep bible, outlines, chapters, and traces in editable Markdown/YAML."],
        [Activity, "Retrieval-aware", "Trigger local vector indexing now; switch to pgvector for shared deployments later."],
        [PenLine, "Agent traceable", "Every orchestrated chapter run keeps role-by-role decisions in runs/."],
      ].map(([Icon, title, body]) => (
        <Card key={String(title)}>
          <CardHeader>
            <Icon className="mb-2 h-5 w-5 text-primary" />
            <CardTitle>{title as string}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-6 text-muted-foreground">{body as string}</CardContent>
        </Card>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
      <div className="font-mono text-[0.65rem] uppercase tracking-wide">{label}</div>
      <div className="mt-1 text-lg font-semibold text-foreground">{value}</div>
    </div>
  );
}
