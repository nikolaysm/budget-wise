# Dockerfile for the Next.js frontend service
#
# This image builds the production version of the Next.js application and
# serves it using the built‑in Next.js server. The build step runs in a
# separate stage to keep the runtime image as small as possible.

FROM node:20-alpine as build

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

COPY package.json pnpm-lock.yaml* /app/
RUN if [ -f pnpm-lock.yaml ]; then \
			pnpm install --frozen-lockfile; \
		else \
			pnpm install; \
		fi

# Copy source code and build
COPY . /app
RUN pnpm build

FROM node:20-alpine as runtime

WORKDIR /app

ENV NODE_ENV=production

RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

# Copy build output and production dependencies
COPY --from=build /app /app

# Expose the frontend port
EXPOSE 3000

# Start the Next.js server
CMD ["pnpm", "start"]