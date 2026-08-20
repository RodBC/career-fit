import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
        // linkedin-session can wait up to ~5 min for login
        timeout: 320_000,
        proxyTimeout: 320_000,
      },
    },
  },
});
