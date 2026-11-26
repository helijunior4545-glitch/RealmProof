import { defineConfig } from "vite";

export default defineConfig(({ mode }) => ({
  // Library mode preserves process.env by default, but Django serves this bundle directly.
  define: { "process.env.NODE_ENV": JSON.stringify(mode === "development" ? "development" : "production") },
  build: {
    outDir: "../studio/static/studio/react",
    emptyOutDir: true,
    lib: {
      entry: "src/landing.tsx",
      formats: ["es"],
      fileName: () => "landing.js",
    },
    rollupOptions: { output: { inlineDynamicImports: true } },
  },
}));
