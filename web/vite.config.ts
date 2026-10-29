import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the same build works on GitHub Pages under /rootcause/ and at the root
// when served by FastAPI.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
});
