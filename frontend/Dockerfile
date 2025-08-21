# Dockerfile for the Next.js frontend service
#
# This image builds the production version of the Next.js application and
# serves it using the built‑in Next.js server. The build step runs in a
# separate stage to keep the runtime image as small as possible.

FROM node:20-alpine as build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* /app/
RUN npm install

# Copy source code and build
COPY . /app
RUN npm run build

FROM node:20-alpine as runtime

WORKDIR /app

ENV NODE_ENV=production

# Copy build output and production dependencies
COPY --from=build /app /app

# Expose the frontend port
EXPOSE 3000

# Start the Next.js server
CMD ["npm", "start"]