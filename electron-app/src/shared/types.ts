export type OutputFormat = "json" | "html" | "csv";

export interface FolderInfo {
  absolutePath: string;
  relativePath: string;
  depth: number;
  fileCount: number;
  comment?: string;
}

export interface ScanResult {
  folders: FolderInfo[];
  warnings: string[];
}

export interface ScanOptions {
  rootPath: string;
  maxDepth: number;
  minFiles: number;
  comments?: Record<string, string>;
}

export interface RunOptions extends ScanOptions {
  formats: OutputFormat[];
  outputBasePath: string;
  existingFilePath?: string;
}

export interface WrittenFiles {
  json?: string;
  html?: string;
  csv?: string;
}

export interface RunResponse {
  result: ScanResult;
  writtenFiles: WrittenFiles;
}

export interface RendererApi {
  selectRootDirectory(): Promise<string | undefined>;
  selectOutputFile(initialPath?: string): Promise<string | undefined>;
  selectExistingFile(): Promise<string | undefined>;
  runScan(options: RunOptions): Promise<RunResponse>;
  openPath(targetPath: string): Promise<void>;
}
