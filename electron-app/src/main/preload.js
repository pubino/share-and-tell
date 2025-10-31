const { contextBridge, ipcRenderer } = require("electron");

const api = {
  async selectRootDirectory() {
    return ipcRenderer.invoke("share-and-tell/select-root");
  },
  async selectOutputFile(initialPath) {
    return ipcRenderer.invoke("share-and-tell/select-output", initialPath);
  },
  async selectExistingFile() {
    return ipcRenderer.invoke("share-and-tell/select-existing");
  },
  async runScan(options) {
    return ipcRenderer.invoke("share-and-tell/run", options);
  },
  async openPath(targetPath) {
    await ipcRenderer.invoke("share-and-tell/open-path", targetPath);
  },
};

contextBridge.exposeInMainWorld("shareAndTell", api);
