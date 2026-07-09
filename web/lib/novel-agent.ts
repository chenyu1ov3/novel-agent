import { readdir, readFile, stat, writeFile } from "node:fs/promises";
import { join, resolve, sep } from "node:path";
import { spawn } from "node:child_process";

export type NovelConfig = {
  title: string;
  genre: string;
  language: string;
  targetWords: number;
  raw: string;
};

export type ProjectFile = {
  path: string;
  name: string;
  group: string;
  size: number;
};

export type ProjectFileGroup = {
  name: string;
  files: ProjectFile[];
};

export type NovelProject = {
  root: string;
  config: NovelConfig;
  files: ProjectFile[];
  groups: ProjectFileGroup[];
};

export type CommandResult = {
  ok: boolean;
  command: string[];
  stdout: string;
  stderr: string;
  exitCode: number | null;
};

const PROJECT_DIRS = ["bible", "outlines", "summaries", "chapters", "scenes", "memory", "runs"];
const TEXT_SUFFIXES = new Set([".md", ".yaml", ".yml", ".json", ".txt"]);

export function rejectUnsafeProjectFile(relativePath: string) {
  if (
    relativePath.startsWith("/") ||
    relativePath.includes("..") ||
    relativePath.split(/[\\/]/).some((part) => part === "" || part === ".")
  ) {
    throw new Error(`Unsafe project file: ${relativePath}`);
  }
}

export async function readNovelProject(projectRoot: string): Promise<NovelProject> {
  const root = resolve(projectRoot);
  const configPath = join(root, "novel.yaml");
  const raw = await readFile(configPath, "utf8");
  const files = await listProjectFiles(root);
  return {
    root,
    config: parseNovelYaml(raw),
    files,
    groups: toProjectFileTree(files),
  };
}

export async function listProjectFiles(projectRoot: string): Promise<ProjectFile[]> {
  const root = resolve(projectRoot);
  const files: ProjectFile[] = [];
  for (const group of PROJECT_DIRS) {
    await collectGroupFiles(root, group, files);
  }
  files.sort((a, b) => a.path.localeCompare(b.path));
  return files;
}

export function toProjectFileTree(files: ProjectFile[]): ProjectFileGroup[] {
  return PROJECT_DIRS.map((name) => ({
    name,
    files: files.filter((file) => file.group === name),
  })).filter((group) => group.files.length > 0);
}

export async function readProjectFile(projectRoot: string, relativePath: string) {
  rejectUnsafeProjectFile(relativePath);
  const target = safeJoin(projectRoot, relativePath);
  return readFile(target, "utf8");
}

export async function writeProjectFile(projectRoot: string, relativePath: string, content: string) {
  rejectUnsafeProjectFile(relativePath);
  const target = safeJoin(projectRoot, relativePath);
  await writeFile(target, content, "utf8");
}

export async function runNovelAgent(projectRoot: string, args: string[]): Promise<CommandResult> {
  const command = process.env.NOVEL_AGENT_BIN ?? "novel-agent";
  return runCommand(command, [...args, projectRoot]);
}

export async function indexMemory(projectRoot: string, backend = "local") {
  return runNovelAgent(projectRoot, ["index-memory", "--backend", backend]);
}

export async function runAgentDraft(projectRoot: string, chapter: number, goal: string) {
  return runNovelAgent(projectRoot, ["agent-run", "--chapter", String(chapter), "--goal", goal]);
}

export function parseNovelYaml(raw: string): NovelConfig {
  const data = Object.fromEntries(
    raw
      .split(/\r?\n/)
      .map((line) => line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/))
      .filter((match): match is RegExpMatchArray => Boolean(match))
      .map((match) => [match[1], match[2].replace(/^['"]|['"]$/g, "")]),
  );
  return {
    title: data.title || "未命名小说",
    genre: data.genre || "未设定",
    language: data.language || "zh-CN",
    targetWords: Number(data.target_words || data.targetWords || 0),
    raw,
  };
}

function safeJoin(projectRoot: string, relativePath: string) {
  const root = resolve(projectRoot);
  const target = resolve(root, relativePath);
  if (target !== root && !target.startsWith(root + sep)) {
    throw new Error(`Unsafe project file: ${relativePath}`);
  }
  return target;
}

async function collectGroupFiles(root: string, group: string, files: ProjectFile[]) {
  const dir = join(root, group);
  try {
    const current = await stat(dir);
    if (!current.isDirectory()) return;
  } catch {
    return;
  }
  await walk(root, dir, group, files);
}

async function walk(root: string, dir: string, group: string, files: ProjectFile[]) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const absolute = join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(root, absolute, group, files);
      continue;
    }
    if (!entry.isFile() || !isTextFile(entry.name)) continue;
    const info = await stat(absolute);
    const relative = absolute.slice(root.length + 1).split(sep).join("/");
    files.push({ path: relative, name: entry.name, group, size: info.size });
  }
}

function isTextFile(name: string) {
  const lower = name.toLowerCase();
  return [...TEXT_SUFFIXES].some((suffix) => lower.endsWith(suffix));
}

function runCommand(command: string, args: string[]) {
  return new Promise<CommandResult>((resolvePromise) => {
    const child = spawn(command, args, { env: process.env });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      resolvePromise({ ok: false, command: [command, ...args], stdout, stderr: error.message, exitCode: null });
    });
    child.on("close", (exitCode) => {
      resolvePromise({ ok: exitCode === 0, command: [command, ...args], stdout, stderr, exitCode });
    });
  });
}
