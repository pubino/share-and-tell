import fs from "fs";
import path from "path";
import { FolderInfo, RunOptions, RunResponse, ScanOptions, ScanResult } from "./types.js";

const { readdir, writeFile, realpath, mkdir } = fs.promises;

type CommentMap = Record<string, string>;

type DirectoryFrame = {
  dirPath: string;
  depth: number;
};

type TreeNode = Map<string, TreeNode>;

export async function scanDirectory({
  rootPath,
  maxDepth,
  minFiles,
  comments,
}: ScanOptions): Promise<ScanResult> {
  if (maxDepth < 0) {
    throw new Error("maxDepth must be zero or greater");
  }
  if (minFiles < 0) {
    throw new Error("minFiles must be zero or greater");
  }

  const resolvedRoot = await realpath(rootPath);
  const commentMap = normaliseComments(comments ?? {}, resolvedRoot);

  const folders: FolderInfo[] = [];
  const warnings: string[] = [];

  const stack: DirectoryFrame[] = [{ dirPath: resolvedRoot, depth: 0 }];

  while (stack.length > 0) {
    const frame = stack.pop();
    if (!frame) {
      continue;
    }
    const { dirPath, depth } = frame;

    if (depth > maxDepth) {
      continue;
    }

    let dirEntries: fs.Dirent[];
    try {
      dirEntries = await readdir(dirPath, { withFileTypes: true });
    } catch (error) {
      warnings.push(`Skipped ${dirPath}: ${(error as Error).message}`);
      continue;
    }

    const fileCount = dirEntries.filter((entry) => entry.isFile()).length;
    if (depth === 0 || fileCount >= minFiles) {
      const comment = commentMap[dirPath] ?? "";
      folders.push({
        absolutePath: dirPath,
        relativePath: toRelativePath(resolvedRoot, dirPath),
        depth,
        fileCount,
        comment,
      });
    }

    const childDirectories = dirEntries
      .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink())
      .map((entry) => path.join(dirPath, entry.name))
      .sort((a, b) => a.localeCompare(b));

    for (let index = childDirectories.length - 1; index >= 0; index -= 1) {
      stack.push({ dirPath: childDirectories[index]!, depth: depth + 1 });
    }
  }

  folders.sort((a, b) => folderLabel(a).localeCompare(folderLabel(b)));

  return { folders, warnings };
}

export async function runAndWrite(options: RunOptions): Promise<RunResponse> {
  const result = await scanDirectory(options);
  const outputs: RunResponse["writtenFiles"] = {};

  const baseFile = basePathWithoutExtension(options.outputBasePath);

  const payloads: Array<{ format: keyof RunResponse["writtenFiles"]; data: string }>
    = [];

  for (const format of options.formats) {
    switch (format) {
      case "json":
        payloads.push({ format, data: renderJson(result, options) });
        break;
      case "html":
        payloads.push({ format, data: renderHtml(result, options) });
        break;
      case "csv":
        payloads.push({ format, data: renderCsv(result) });
        break;
      default:
        break;
    }
  }

  for (const payload of payloads) {
    const targetPath = `${baseFile}.${payload.format}`;
    await mkdir(path.dirname(targetPath), { recursive: true });
    await writeFile(targetPath, payload.data, "utf-8");
    outputs[payload.format] = targetPath;
  }

  return { result, writtenFiles: outputs };
}

export function renderJson(result: ScanResult, options: ScanOptions): string {
  const document = {
    generated_at: new Date().toISOString(),
    root: path.resolve(options.rootPath),
    max_depth: options.maxDepth,
    min_files: options.minFiles,
    folders: result.folders.map((folder) => ({
      folder: folderLabel(folder),
      absolute_path: folder.absolutePath,
      depth: folder.depth,
      file_count: folder.fileCount,
      comment: folder.comment ?? "",
    })),
    warnings: result.warnings,
  };

  return JSON.stringify(document, null, 2);
}

export function renderCsv(result: ScanResult): string {
  const lines = ["folder,absolute_path,depth,file_count,comment"];
  for (const folder of [...result.folders].sort((a, b) => folderLabel(a).localeCompare(folderLabel(b)))) {
    const row = [
      csvEscape(folderLabel(folder)),
      csvEscape(folder.absolutePath),
      folder.depth.toString(10),
      folder.fileCount.toString(10),
      csvEscape(folder.comment ?? ""),
    ];
    lines.push(row.join(","));
  }
  return `${lines.join("\n")}\n`;
}

export function renderHtml(result: ScanResult, options: ScanOptions): string {
  const folders = [...result.folders].sort((a, b) => folderLabel(a).localeCompare(folderLabel(b)));
  const tree = buildTree(folders);
  const outlineBody = renderOutline(tree);
  const rootInfo = folders.find((folder) => folder.relativePath === ".");
  const rootComment = rootInfo?.comment ? `<span class="comment">${escapeHtml(rootInfo.comment)}</span>` : "";
  const outlineHtml = `
    <div class="outline-root">
      <span class="folder">${escapeHtml(path.basename(path.resolve(options.rootPath)) || options.rootPath)}</span>
      ${rootComment}
      ${outlineBody}
    </div>
  `;

  const rows = folders
    .map(
      (folder) => `
        <tr>
          <td>${escapeHtml(folderLabel(folder))}</td>
          <td class="num">${folder.depth}</td>
          <td class="num">${folder.fileCount}</td>
          <td>${escapeHtml(folder.comment ?? "")}</td>
        </tr>
      `,
    )
    .join("\n");

  const warningsHtml = result.warnings.length
    ? `<section><h2>Warnings</h2><ul class="warnings">${result.warnings
        .map((warning) => `<li>${escapeHtml(warning)}</li>`)
        .join("")}</ul></section>`
    : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Share and Tell Report</title>
  <style>
    body { font-family: 'Segoe UI', Roboto, sans-serif; margin: 2rem; color: #222; background: #f8f9fb; }
    h1, h2 { color: #2f3c70; }
    table { border-collapse: collapse; width: 100%; max-width: 960px; margin-bottom: 2rem; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
    th, td { border: 1px solid #dee2ed; padding: 0.6rem 0.9rem; text-align: left; }
    th { background-color: #eef2fb; font-weight: 600; }
    td.num { text-align: right; width: 4rem; }
    ul { list-style-type: none; padding-left: 1.25rem; margin: 0; }
    ul ul { border-left: 1px solid #cbd3eb; margin-left: 0.5rem; padding-left: 1.25rem; }
    .comment { color: #5b5f7a; margin-left: 0.5rem; font-style: italic; }
    .warnings { color: #b02a37; }
    .metadata { margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; gap: 1rem; }
    .metadata span { display: inline-flex; align-items: center; background: #fff; border-radius: 999px; padding: 0.4rem 0.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .outline-root > .folder { font-weight: 600; }
    .outline-root { margin-left: 0.25rem; background: #fff; padding: 1rem; border-radius: 0.75rem; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
  </style>
</head>
<body>
  <h1>Share and Tell Report</h1>
  <section class="metadata">
    <span><strong>Root:</strong>&nbsp;${escapeHtml(path.resolve(options.rootPath))}</span>
    <span><strong>Max Depth:</strong>&nbsp;${options.maxDepth}</span>
    <span><strong>Min Files:</strong>&nbsp;${options.minFiles}</span>
    <span><strong>Generated:</strong>&nbsp;${escapeHtml(new Date().toISOString())}</span>
  </section>
  <section>
    <h2>Folder Summary</h2>
    <table>
      <thead>
        <tr><th>Folder</th><th>Depth</th><th>Files</th><th>Comment</th></tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  </section>
  <section>
    <h2>Outline View</h2>
    ${outlineHtml}
  </section>
  ${warningsHtml}
</body>
</html>`;
}

function buildTree(folders: FolderInfo[]): TreeNode {
  const tree: TreeNode = new Map();
  for (const folder of folders) {
    const parts = folderLabel(folder) === "." ? [] : folderLabel(folder).split("/");
    let cursor = tree;
    for (const part of parts) {
      if (!cursor.has(part)) {
        cursor.set(part, new Map());
      }
      const next = cursor.get(part)!;
      cursor = next;
    }
  }
  return tree;
}

function folderLabel(folder: FolderInfo): string {
  const label = folder.relativePath.replace(/\\/g, "/");
  return label.length > 0 ? label : ".";
}

function toRelativePath(root: string, target: string): string {
  const relative = path.relative(root, target);
  return relative ? relative.split(path.sep).join("/") : ".";
}

function normaliseComments(comments: CommentMap, root: string): CommentMap {
  const next: CommentMap = {};
  for (const [key, value] of Object.entries(comments)) {
    const resolved = path.isAbsolute(key) ? key : path.join(root, key);
    next[path.resolve(resolved)] = value;
  }
  return next;
}

function basePathWithoutExtension(filePath: string): string {
  const parsed = path.parse(filePath);
  return path.join(parsed.dir, parsed.name);
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function renderOutline(tree: TreeNode): string {
  if (tree.size === 0) {
    return "<p>No folders met the criteria.</p>";
  }
  const entries = [...tree.entries()].sort((a, b) => a[0]!.localeCompare(b[0]!));
  const items = entries
    .map(([name, child]) => {
      const childNodes = renderOutline(child);
      return `<li><span class="folder">${escapeHtml(name)}</span>${childNodes}</li>`;
    })
    .join("");
  return `<ul>${items}</ul>`;
}