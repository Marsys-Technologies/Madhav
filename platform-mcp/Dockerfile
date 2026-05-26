# platform-mcp — MARSYS-JIS MCP Server (multi-stage build)
# Stage 1: compile TypeScript; Stage 2: production-only deps + compiled output.
#
# Build context: repo root (so COPY can reach 025_HOLISTIC_SYNTHESIS/, 01_FACTS_LAYER/, etc.)
# Cloud Build invokes: docker build -f platform-mcp/Dockerfile .
# All COPY sources are prefixed with platform-mcp/ or reference repo-root directories.

FROM node:20-alpine AS builder
WORKDIR /build
COPY platform-mcp/package*.json ./
RUN npm ci
COPY platform-mcp/tsconfig.json ./
COPY platform-mcp/src/ ./src/
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY platform-mcp/package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /build/dist ./dist
COPY platform-mcp/resources/ ./resources/
# Canonical markdown corpus required by read_asset and file-based retrieval tools
COPY 025_HOLISTIC_SYNTHESIS/ ./025_HOLISTIC_SYNTHESIS/
COPY 01_FACTS_LAYER/ ./01_FACTS_LAYER/
COPY 00_ARCHITECTURE/MACRO_PLAN_v2_0.md ./00_ARCHITECTURE/MACRO_PLAN_v2_0.md
COPY 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md ./00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
COPY 00_ARCHITECTURE/CURRENT_STATE_v1_0.md ./00_ARCHITECTURE/CURRENT_STATE_v1_0.md
EXPOSE 8080
CMD ["node", "dist/server.js"]
