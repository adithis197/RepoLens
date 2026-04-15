import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import fs from "fs";

function copyExtensionFiles() {
  return {
    name: "copy-extension-files",
    closeBundle() {
      fs.copyFileSync("manifest.json", "dist/manifest.json");
      if (fs.existsSync("public")) {
        fs.cpSync("public", "dist", { recursive: true });
      }
      if (fs.existsSync("assets")) {
        fs.cpSync("assets", "dist/assets", { recursive: true });
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), copyExtensionFiles()],
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    target: "chrome114",
    modulePreload: false,
    rollupOptions: {
      input: {
        popup: resolve(__dirname, "popup.html"),
        background: resolve(__dirname, "src/background.js"),
        content: resolve(__dirname, "src/content.js"),
      },
      output: {
        format: "es",
        entryFileNames: "src/[name].js",
        chunkFileNames: "src/[name].js",
        assetFileNames: "[name].[ext]",
      },
    },
  },
});