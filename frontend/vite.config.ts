import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" keeps every asset path relative, so the built dist/ folder
// can be dropped on Netlify, Vercel, GitHub Pages or any sub-path as is.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    port: 5173
  }
});
