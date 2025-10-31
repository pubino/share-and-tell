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
  maxRetries?: number;
  retryDelay?: number;
  onProgress?: (progress: ScanProgress) => void;
  signal?: AbortSignal;
}

export interface ScanProgress {
  foldersProcessed: number;
  directoriesScanned: number;
  totalFilesFound: number;
  currentPath?: string;
  warningsCount: number;
  retryCount: number;
}

export interface RunOptions extends ScanOptions {
  formats: OutputFormat[];
  outputBasePath: string;
  existingFilePath?: string;
  signal?: AbortSignal;
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
