# Build context is ./frontend.
#
#   docker build -f frontend/Dockerfile frontend
#
# The app has no NEXT_PUBLIC_* variables: every browser request goes to the
# same-origin Next.js proxy at app/api/[...path]/route.ts, which reads
# INTERNAL_API_BASE_URL at runtime. That makes this a single-stage-friendly
# build with no build-time API URL to bake in.

FROM node:24-alpine AS builder

WORKDIR /app

# Tailwind v4 and Next both need the lockfile-exact tree.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build


FROM node:24-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# No `output: "standalone"` in next.config.ts, so the runtime needs the full
# node_modules tree and the built .next directory.
COPY --from=builder /app/package.json /app/package-lock.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# next.config.ts is deliberately not copied: it only switches distDir for the
# local verification harness, and the default `.next` is what was built here.
# Leaving it out also avoids needing TypeScript at runtime.

# Next writes its cache into .next/cache at runtime.
RUN mkdir -p /app/.next/cache && chown -R node:node /app/.next/cache
USER node

EXPOSE 3000

# Bind explicitly: the default hostname differs between Next versions.
CMD ["./node_modules/.bin/next", "start", "-H", "0.0.0.0", "-p", "3000"]
