import { contextBridge, ipcRenderer } from "electron";
import type { RendererApi, RunOptions, RunResponse } from "../shared/types.js";

const api: RendererApi = {
  async selectRootDirectory(): Promise<string | undefined> {
    return ipcRenderer.invoke("share-and-tell/select-root");
  },
  async selectOutputFile(initialPath?: string): Promise<string | undefined> {
    return ipcRenderer.invoke("share-and-tell/select-output", initialPath);
  },
  async runScan(options: RunOptions): Promise<RunResponse> {
    return ipcRenderer.invoke("share-and-tell/run", options);
  },
  async openPath(targetPath: string): Promise<void> {
    await ipcRenderer.invoke("share-and-tell/open-path", targetPath);
  },
};

contextBridge.exposeInMainWorld("shareAndTell", api);
