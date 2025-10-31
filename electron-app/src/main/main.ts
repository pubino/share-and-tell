import { app, BrowserWindow, dialog, ipcMain, shell } from "electron";
import type { IpcMainInvokeEvent, IpcMainEvent } from "electron";
import path from "path";
import { fileURLToPath } from "url";
import { runAndWrite } from "../shared/shareAndTell.js";
import { RunOptions, RunResponse } from "../shared/types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function createWindow(): Promise<void> {
  const window = new BrowserWindow({
    width: 1100,
    height: 760,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  await window.loadFile(path.join(__dirname, "../renderer/index.html"));

  window.on("ready-to-show", () => {
    window.show();
  });
}

authenticateIpcHandlers();

app.whenReady().then(createWindow).catch((error: unknown) => {
  console.error("Failed to create window", error);
  app.quit();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", async () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    await createWindow();
  }
});

function authenticateIpcHandlers(): void {
  ipcMain.handle("share-and-tell/select-root", async () => {
    const result = await dialog.showOpenDialog({
      properties: ["openDirectory"],
      title: "Select the folder to scan",
    });
    if (result.canceled || result.filePaths.length === 0) {
      return undefined;
    }
    return result.filePaths[0];
  });

  ipcMain.handle("share-and-tell/select-output", async (
    _event: IpcMainInvokeEvent,
    initialPath?: string,
  ) => {
    const result = await dialog.showSaveDialog({
      title: "Choose the base file name for the report",
      defaultPath: initialPath,
      filters: [
        { name: "All formats", extensions: ["json", "html", "csv"] },
      ],
    });
    if (result.canceled || !result.filePath) {
      return undefined;
    }
    return result.filePath;
  });

  ipcMain.handle("share-and-tell/run", async (
    _event: IpcMainInvokeEvent,
    options: RunOptions,
  ) => {
    const response: RunResponse = await runAndWrite(options);
    return response;
  });

  ipcMain.handle("share-and-tell/open-path", async (
    _event: IpcMainInvokeEvent,
    targetPath: string,
  ) => {
    if (!targetPath) {
      return;
    }
    shell.showItemInFolder(targetPath);
  });
}
