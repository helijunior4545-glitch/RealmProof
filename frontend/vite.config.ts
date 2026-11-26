import { defineConfig } from "vite";
export default defineConfig({build:{outDir:"../studio/static/studio/react",emptyOutDir:true,lib:{entry:"src/landing.tsx",formats:["es"],fileName:()=>"landing.js"},rollupOptions:{output:{inlineDynamicImports:true}}}});
