import type { RendererApi } from "../shared/types.js";

declare global {
  interface Window {
    shareAndTell: RendererApi;
  }
}

export {};
