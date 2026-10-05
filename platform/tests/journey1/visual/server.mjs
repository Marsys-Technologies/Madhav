// Local component verification only. Does not configure or bypass application auth.
import { createServer } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
const root = process.cwd();
const server = await createServer({
  configFile: false,
  root,
  plugins: [
    react(),
    {
      name: "no-fixture-submissions",
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url?.startsWith("/api/")) {
            res.statusCode = 403;
            res.end("Component tests cannot submit requests");
            return;
          }
          next();
        });
      },
    },
  ],
  resolve: {
    alias: {
      "@": path.join(root, "src"),
      "next/link": path.join(root, "tests/journey1/visual/navigation.tsx"),
      "next/navigation": path.join(
        root,
        "tests/journey1/visual/navigation.tsx",
      ),
    },
  },
  define: { "process.env": {} },
  server: { host: "127.0.0.1", port: 3188, strictPort: true },
});
await server.listen();
console.log(
  "Component verification: http://127.0.0.1:3188/tests/journey1/visual/index.html",
);
