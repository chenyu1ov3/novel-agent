import { NextResponse } from "next/server";
import { indexMemory } from "@/lib/novel-agent";

export async function POST(request: Request) {
  const body = (await request.json()) as { projectPath?: string; backend?: string };
  const projectPath = body.projectPath || process.env.NOVEL_AGENT_PROJECT;
  if (!projectPath) {
    return NextResponse.json({ error: "Missing projectPath" }, { status: 400 });
  }

  const result = await indexMemory(projectPath, body.backend || "local");
  return NextResponse.json(result, { status: result.ok ? 200 : 500 });
}
