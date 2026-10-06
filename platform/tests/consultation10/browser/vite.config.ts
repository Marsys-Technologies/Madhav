import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
const base = fileURLToPath(new URL("../../../", import.meta.url));
export default defineConfig({
  root: base,
  publicDir: `${base}public`,
  plugins: [react()],
  define: {
    "process.env": JSON.stringify({
      NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK: "false",
      NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED: "false",
    }),
  },
  resolve: {
    alias: {
      "next/navigation": `${base}tests/consultation10/browser/navigation.ts`,
      "next/link": `${base}tests/consultation10/browser/link.tsx`,
      "@": `${base}src`,
    },
  },
  server: { host: "127.0.0.1", port: 3188, strictPort: true },
});
