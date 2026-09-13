FROM node:24-alpine AS builder

WORKDIR /app

# NEXT_PUBLIC_* values are inlined into the bundle at build time, so setting
# this only in the runtime environment would have no effect.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build


FROM node:24-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/package.json /app/package-lock.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

# `next start` rather than `next dev`: the container should prove the app
# compiles, not just that it runs unbuilt.
CMD ["npm", "start"]
