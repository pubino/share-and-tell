import type { OutputFormat, RunOptions, RunResponse } from "../shared/types.js";

const form = document.getElementById("scan-form") as HTMLFormElement;
const rootInput = document.getElementById("root-input") as HTMLInputElement;
const outputInput = document.getElementById("output-input") as HTMLInputElement;
const existingInput = document.getElementById("existing-input") as HTMLInputElement;
const statusText = document.getElementById("status-text") as HTMLSpanElement;
const resultsContainer = document.getElementById("results") as HTMLElement;
const progressContainer = document.getElementById("progress-container") as HTMLElement;

const browseRootButton = document.querySelector<HTMLButtonElement>(
  'button[data-action="select-root"]',
);
const browseOutputButton = document.querySelector<HTMLButtonElement>(
  'button[data-action="select-output"]',
);
const browseExistingButton = document.querySelector<HTMLButtonElement>(
  'button[data-action="select-existing"]',
);
const cancelButton = document.getElementById("cancel-button") as HTMLButtonElement;

let lastRunResponse: RunResponse | null = null;
let currentAbortController: AbortController | null = null;

renderEmptyState();

browseRootButton?.addEventListener("click", async () => {
  const directory = await window.shareAndTell.selectRootDirectory();
  if (directory) {
    rootInput.value = directory;
    setStatus("");
  }
});

browseOutputButton?.addEventListener("click", async () => {
  const outputPath = await window.shareAndTell.selectOutputFile(outputInput.value.trim() || undefined);
  if (outputPath) {
    outputInput.value = outputPath;
    setStatus("");
  }
});

browseExistingButton?.addEventListener("click", async () => {
  const existingPath = await window.shareAndTell.selectExistingFile();
  if (existingPath) {
    existingInput.value = existingPath;
    setStatus("");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const rootPath = rootInput.value.trim();
  const outputPath = outputInput.value.trim();
  const existingPath = existingInput.value.trim();
  const maxDepth = Number((document.getElementById("depth-input") as HTMLInputElement).value);
  const minFiles = Number((document.getElementById("files-input") as HTMLInputElement).value);
  const formats = collectFormats();

  if (!rootPath) {
    setStatus("Please choose a folder to analyse.");
    return;
  }
  if (!outputPath) {
    setStatus("Please choose where to save the report.");
    return;
  }
  if (formats.length === 0) {
    setStatus("Select at least one output format.");
    return;
  }

  try {
    disableForm(true);
    showProgress();
    showCancelButton();
    setStatus("Scanning…");

    currentAbortController = new AbortController();

    const options: RunOptions = {
      rootPath,
      outputBasePath: outputPath,
      maxDepth: Number.isFinite(maxDepth) ? maxDepth : 3,
      minFiles: Number.isFinite(minFiles) ? minFiles : 3,
      formats,
      comments: {},
      existingFilePath: existingPath || undefined,
      signal: currentAbortController.signal,
    };

    const response = await window.shareAndTell.runScan(options);
    lastRunResponse = response;
    renderSuccess(response);
    setStatus("Report generated successfully.");
  } catch (error) {
    const err = error as Error;
    if (err.name === "AbortError" || err.message.includes("cancelled")) {
      setStatus("Scan cancelled.");
    } else {
      console.error(error);
      setStatus(`Unable to generate the report: ${err.message}`);
    }
  } finally {
    disableForm(false);
    hideProgress();
    hideCancelButton();
    currentAbortController = null;
  }
});

cancelButton.addEventListener("click", () => {
  if (currentAbortController) {
    currentAbortController.abort();
    setStatus("Cancelling scan...");
  }
});

function collectFormats(): OutputFormat[] {
  const inputs = form.querySelectorAll<HTMLInputElement>('input[name="format"]');
  const selected: OutputFormat[] = [];
  inputs.forEach((input) => {
    if (input.checked) {
      selected.push(input.value as OutputFormat);
    }
  });
  return selected;
}

function disableForm(state: boolean): void {
  const elements = form.querySelectorAll<HTMLInputElement | HTMLButtonElement>("input, button");
  elements.forEach((element) => {
    element.disabled = state;
  });
}

function setStatus(message: string): void {
  statusText.textContent = message;
}

function showProgress(): void {
  progressContainer.style.display = "flex";
}

function hideProgress(): void {
  progressContainer.style.display = "none";
}

function showCancelButton(): void {
  cancelButton.style.display = "inline-block";
}

function hideCancelButton(): void {
  cancelButton.style.display = "none";
}

function renderEmptyState(): void {
  resultsContainer.innerHTML = "";
  const placeholder = document.createElement("div");
  placeholder.className = "results__empty";
  placeholder.innerHTML = `
    <p class="results__warning">This app aggregates folder names, file counts, and comments. Please store and share this data with the appropriate level of protection.  Seek asssistance if you are uncertain what level is necessary.</p>
    <h2>Ready when you are</h2>
    <p>Select a folder to analyse, choose your output formats, and Share and Tell will do the rest.</p>
  `;
  resultsContainer.appendChild(placeholder);
}

function renderSuccess(response: RunResponse): void {
  const folderCount = response.result.folders.length;
  const warnings = response.result.warnings;
  const writtenFiles = response.writtenFiles;

  const fileEntries = Object.entries(writtenFiles) as Array<[OutputFormat, string]>;

  const fileList = fileEntries.length
    ? `<ul class="result-list">
        ${fileEntries
          .map(
            ([format, filePath]) => `
              <li>
                <div><strong>${format.toUpperCase()}</strong> saved to <code>${escapeHtml(filePath)}</code></div>
                <button type="button" data-open="${escapeAttribute(filePath)}">Show in Finder / Explorer</button>
              </li>
            `,
          )
          .join("")}
       </ul>`
    : `<p>No files were written.</p>`;

  const warningList = warnings.length
    ? `<section>
        <h3>Warnings</h3>
        <ul class="warning-list">
          ${warnings.map((message) => `<li>${escapeHtml(message)}</li>`).join("")}
        </ul>
      </section>`
    : "";

  resultsContainer.innerHTML = `
    <article class="result-card">
      <h2>Scan summary</h2>
      <div class="result-grid">
        <div class="result-pill">${folderCount} folders captured</div>
        <div class="result-pill">${warnings.length} warnings</div>
      </div>
    </article>
    <section>
      <h3>Generated files</h3>
      ${fileList}
    </section>
    ${warningList}
  `;

  resultsContainer.querySelectorAll<HTMLButtonElement>("button[data-open]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetPath = button.dataset.open;
      if (targetPath) {
        void window.shareAndTell.openPath(targetPath);
      }
    });
  });
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}

function escapeAttribute(value: string): string {
  return escapeHtml(value).replace(/`/g, "&#x60;");
}

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && lastRunResponse) {
    renderEmptyState();
    lastRunResponse = null;
    setStatus("Cleared the results.");
  }
});