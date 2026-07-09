import { NextResponse } from "next/server";
import { readNovelProject } from "@/lib/novel-agent";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectPath = searchParams.get("path") || process.env.NOVEL_AGENT_PROJECT;
  if (!projectPath) {
    return NextResponse.json({ error: "Missing project path" }, { status: 400 });
  }

  try {
    return NextResponse.json(await readNovelProject(projectPath));
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to read project" },
      { status: 500 },
    );
  }
}
