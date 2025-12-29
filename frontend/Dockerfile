# =============================================================================
# AESA Frontend Dockerfile
# Multi-stage build for Next.js production image
# Requirements: 27.1, 27.6
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Dependencies
# Install all npm dependencies for building
# -----------------------------------------------------------------------------
FROM node:20-alpine AS deps

WORKDIR /app

# Install libc6-compat for Alpine compatibility
RUN apk add --no-cache libc6-compat

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies with clean install
RUN npm ci --only=production=false

# -----------------------------------------------------------------------------
# Stage 2: Builder
# Build the Next.js application
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source files
COPY frontend/ .

# Set build-time environment variables
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Increase Node.js memory limit for build
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Skip ESLint during build (already checked in CI)
ENV NEXT_LINT_DURING_BUILD=false

# Set dummy API URL for build time (will be overridden at runtime)
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Build the application with standalone output
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Production Runner
# Minimal image with only production assets
# -----------------------------------------------------------------------------
FROM node:20-alpine AS runner

WORKDIR /app

# Labels for container registry
LABEL org.opencontainers.image.title="AESA Frontend"
LABEL org.opencontainers.image.description="AI Engineering Study Assistant - Next.js Frontend"
LABEL org.opencontainers.image.vendor="AESA Project"
LABEL org.opencontainers.image.source="https://github.com/aesa/aesa-core-scheduling"

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy public assets
COPY --from=builder /app/public ./public

# Set correct permissions for prerender cache
RUN mkdir .next && chown nextjs:nodejs .next

# Copy standalone build output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start the application
CMD ["node", "server.js"]
