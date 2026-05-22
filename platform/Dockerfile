FROM node:20-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# Repo root for any code path that resolves files under 00_ARCHITECTURE
# during `next build`. Builder cwd=/app, and `path.join(cwd,'..',…)` would
# escape to the filesystem root and ENOENT — see manifest_planner.ts.
ENV MARSYS_REPO_ROOT=/app
ARG NEXT_PUBLIC_FIREBASE_API_KEY
ENV NEXT_PUBLIC_FIREBASE_API_KEY=$NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ENV NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ENV NEXT_PUBLIC_FIREBASE_PROJECT_ID=$NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
ENV NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=$NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
ARG NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
ENV NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=$NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
ARG NEXT_PUBLIC_FIREBASE_APP_ID
ENV NEXT_PUBLIC_FIREBASE_APP_ID=$NEXT_PUBLIC_FIREBASE_APP_ID
ARG BUILD_STATE_GCS_BASE
ENV BUILD_STATE_GCS_BASE=$BUILD_STATE_GCS_BASE
ARG NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY
ENV NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=$NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY
ARG NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL
ENV NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL=$NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV MARSYS_REPO_ROOT=/app
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/00_ARCHITECTURE ./00_ARCHITECTURE
# L3 register JSON files — required by pattern_register, resonance_register,
# cluster_atlas, contradiction_register retrieval tools at query time.
# Without this, those 4 tools throw ENOENT silently and return null bundles.
COPY --from=builder --chown=nextjs:nodejs /app/035_DISCOVERY_LAYER ./035_DISCOVERY_LAYER
# L1 facts + L2.5 holistic synthesis corpus — bundle_hydrator floor assets
# (FORENSIC, CGM) and optional assets (UCN, CDLM, RM, LEL) read at query time.
COPY --from=builder --chown=nextjs:nodejs /app/01_FACTS_LAYER ./01_FACTS_LAYER
COPY --from=builder --chown=nextjs:nodejs /app/025_HOLISTIC_SYNTHESIS ./025_HOLISTIC_SYNTHESIS
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
