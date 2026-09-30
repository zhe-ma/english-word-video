import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = process.env.VV_API || "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@video": path.resolve(__dirname, "../video/src") },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": api,
      "/media": api,
      "/fonts": api,
    },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
