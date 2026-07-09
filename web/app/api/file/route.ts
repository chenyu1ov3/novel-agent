import { NextResponse } from "next/server";
import { readProjectFile, writeProjectFile } from "@/lib/novel-agent";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectPath = searchParams.get("projectPath") || process.env.NOVEL_AGENT_PROJECT;
  const filePath = searchParams.get("filePath");
  if (!projectPath || !filePath) {
    return NextResponse.json({ error: "Missing projectPath or filePath" }, { status: 400 });
  }

  try {
    return NextResponse.json({ path: filePath, content: await readProjectFile(projectPath, filePath) });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to read file" },
      { status: 500 },
    );
  }
}

export async function PUT(request: Request) {
  const body = (await request.json()) as { projectPath?: string; filePath?: string; content?: string };
  const projectPath = body.projectPath || process.env.NOVEL_AGENT_PROJECT;
  if (!projectPath || !body.filePath || body.content === undefined) {
    return NextResponse.json({ error: "Missing projectPath, filePath, or content" }, { status: 400 });
  }

  try {
    await writeProjectFile(projectPath, body.filePath, body.content);
    return NextResponse.json({ ok: true });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to write file" },
      { status: 500 },
    );
  }
}
