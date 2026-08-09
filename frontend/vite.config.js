import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Standard Vite + React setup.
// Dev server runs on http://localhost:5173 by default, which is
// already whitelisted in the FastAPI backend's CORS settings.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
