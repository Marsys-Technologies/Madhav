# platform-mcp — MARSYS-JIS MCP Server (multi-stage build)
# Stage 1: compile TypeScript; Stage 2: production-only deps + compiled output.

FROM node:20-alpine AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /build/dist ./dist
COPY src/resources/*.md ./resources/
EXPOSE 8080
CMD ["node", "dist/server.js"]
