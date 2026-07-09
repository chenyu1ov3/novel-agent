import { createDataStreamResponse } from "ai";
import { runAgentDraft } from "@/lib/novel-agent";

export async function POST(request: Request) {
  const body = (await request.json()) as { projectPath?: string; chapter?: number; goal?: string };
  const projectPath = body.projectPath || process.env.NOVEL_AGENT_PROJECT;
  if (!projectPath) {
    return Response.json({ error: "Missing projectPath" }, { status: 400 });
  }

  return createDataStreamResponse({
    execute: async (dataStream) => {
      dataStream.writeData({ type: "status", message: "Starting multi-agent chapter run" });
      const result = await runAgentDraft(projectPath, body.chapter || 1, body.goal || "按章节大纲推进剧情");
      dataStream.writeData({ type: "command", command: result.command, ok: result.ok });
      dataStream.writeData({ type: "stdout", content: result.stdout });
      if (result.stderr) {
        dataStream.writeData({ type: "stderr", content: result.stderr });
      }
      dataStream.writeData({ type: "done", exitCode: result.exitCode });
    },
  });
}
