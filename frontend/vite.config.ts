import { defineConfig } from "vite";

export default defineConfig({
  // Django serves the library bundle directly in the browser.
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: "../studio/static/studio/react",
    emptyOutDir: true,
    lib: { entry: "src/landing.tsx", formats: ["es"], fileName: () => "landing.js" },
    rollupOptions: { output: { inlineDynamicImports: true } },
  },
});
