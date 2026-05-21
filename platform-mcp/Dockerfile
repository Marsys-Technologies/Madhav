# platform-mcp — MARSYS-JIS MCP Server
# Node 20 Alpine image. The MCP server is a thin adapter; all heavy logic runs
# on the platform (amjis-web). 512 MB RAM is sufficient.

FROM node:20-alpine

WORKDIR /app

# Copy package files first to leverage Docker layer caching
COPY package*.json ./

# Install production dependencies only (dev deps are not needed at runtime)
RUN npm ci --omit=dev

# Copy compiled TypeScript output (built before Docker build via cloudbuild.yaml)
COPY dist/ ./dist/

# Cloud Run default port
EXPOSE 8080

# Start the MCP server
CMD ["node", "dist/server.js"]
