# syntax=docker/dockerfile:1
# This image builds the production version of the Next.js application and
# serves it using the built‑in Next.js server. The build step runs in a
# separate stage to keep the runtime image as small as possible.

FROM node:20-alpine AS base

######## deps ########
FROM base AS deps
WORKDIR /app
RUN apk add --no-cache libc6-compat
# pnpm via corepack
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

# Install deps (full, because we need dev deps to build)
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

######## build ########
FROM base AS builder

WORKDIR /app

RUN apk add --no-cache libc6-compat

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

# Copy node_modules from deps stage
COPY . .
COPY --from=deps /app/node_modules ./node_modules

# Build the application
RUN pnpm build

RUN echo "Build output:"
RUN ls -la ./
RUN ls -la ./.next
RUN pwd
RUN echo "Contents end"

######## runtime ########
FROM base AS runner

WORKDIR /app

ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000

# create non-root user once
ARG UID=10001
RUN addgroup -S nextjs \
 && adduser -S -D -H -h /app -s /sbin/nologin -G nextjs -u ${UID} nextjs

# Copy build artifacts + production deps + pnpm store (needed for pnpm-style symlinks)
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /app/public ./public

USER nextjs

RUN echo "Build output:"
RUN ls -la ./
RUN ls -la ./.next
RUN pwd
RUN echo "Contents end"

EXPOSE 3000

RUN echo "Starting server..."
RUN ls /app/server.js


CMD ["node", "/app/server.js"]
