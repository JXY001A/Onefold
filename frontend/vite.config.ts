import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 本地后端固定跑 8001（8000 常被 IDE 预览占用），与 .vscode/launch.json 保持一致
      "/api": "http://127.0.0.1:8001",
      "/mcp": "http://127.0.0.1:8001",
    },
  },
});
