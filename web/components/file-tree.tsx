"use client";

import { FileText } from "lucide-react";
import type { ProjectFileGroup } from "@/lib/novel-agent";
import { Button } from "@/components/ui/button";
import { useNovelWorkspace } from "@/store/novel-workspace";
import { cn } from "@/lib/utils";

export function FileTree({ groups }: { groups: ProjectFileGroup[] }) {
  const selectedFile = useNovelWorkspace((state) => state.selectedFile);
  const selectFile = useNovelWorkspace((state) => state.selectFile);

  return (
    <div className="space-y-5">
      {groups.map((group) => (
        <section key={group.name} className="space-y-2">
          <div className="font-mono text-xs uppercase tracking-wide text-muted-foreground">{group.name}</div>
          <div className="space-y-1">
            {group.files.map((file) => (
              <Button
                key={file.path}
                variant="ghost"
                className={cn(
                  "h-auto w-full justify-start gap-2 px-2 py-2 text-left text-xs",
                  selectedFile === file.path && "bg-white/[0.06] text-foreground",
                )}
                onClick={() => selectFile(file.path)}
              >
                <FileText className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{file.path}</span>
              </Button>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
