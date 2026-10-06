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
      NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK: "true",
      NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED: "true",
    }),
  },
  resolve: {
    alias: {
      "next/navigation": `${base}tests/account/browser/navigation.ts`,
      "next/link": `${base}tests/account/browser/link.tsx`,
      "@/lib/account/password-flow": `${base}tests/account/browser/password-flow.ts`,
      "@": `${base}src`,
    },
  },
  server: { host: "127.0.0.1", port: 3195, strictPort: true },
});
