# =============================================================================
# AESA Backend Dockerfile
# Multi-stage build with C engine compilation
# Requirements: 27.2, 27.3, 27.6
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: C Engine Builder
# Compiles the C-based constraint satisfaction scheduler
# -----------------------------------------------------------------------------
FROM gcc:13-bookworm AS c-builder

WORKDIR /build

# Copy C engine source files
COPY engine/src/ ./src/
COPY engine/Makefile ./

# Build the C engine with optimizations
RUN make clean 2>/dev/null || true && make all

# Verify the binary was created
RUN test -f scheduler && echo "C engine built successfully"

# -----------------------------------------------------------------------------
# Stage 2: Python Dependencies Builder
# Installs Python packages in a separate stage for caching
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS python-builder

WORKDIR /app

# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Production Runtime
# Minimal image with only runtime dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS production

# Labels for container registry
LABEL org.opencontainers.image.title="AESA Backend"
LABEL org.opencontainers.image.description="AI Engineering Study Assistant - FastAPI Backend with C Scheduler"
LABEL org.opencontainers.image.vendor="AESA Project"
LABEL org.opencontainers.image.source="https://github.com/aesa/aesa-core-scheduling"

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from python-builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy C engine binary from c-builder
COPY --from=c-builder /build/scheduler /app/engine/scheduler
RUN chmod +x /app/engine/scheduler

# Copy application code
COPY backend/app /app/app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV ENGINE_PATH=/app/engine/scheduler

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Health check using curl (more reliable than Python import)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
