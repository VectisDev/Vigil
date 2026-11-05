FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install only runtime system dependencies (no build-essential in final image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# --- Frontend builder stage: build React app with Node.js ---
# NOTA: la etapa frontend-builder se elimino: copiaba de dashboard/frontend/,
# que no existe en este repositorio, por lo que la imagen no podia construirse.
# NOTE: the frontend-builder stage was removed: it copied from
# dashboard/frontend/, which does not exist in this repository, so the
# image could not build at all.


# --- Python builder stage: install Python deps in isolation ---
FROM base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/prod.txt ./requirements/prod.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements/prod.txt

# --- Runtime stage ---
FROM base AS runtime

# Security: non-root user.
RUN groupadd -r vigil && useradd -r -g vigil -d /app -s /sbin/nologin vigil

# Copy installed Python packages from builder.
COPY --from=builder /install /usr/local

# EN: Cache-bust ARG in runtime stage to force layer invalidation.
# ES: ARG para romper cache en stage runtime y forzar invalidación de capas.
ARG CACHE_BUST=0

# Copy application source.
COPY . /app

# EN: Write build marker for runtime verification via /live or SSH.
# ES: Escribir marcador de build para verificación en runtime vía /live o SSH.
RUN echo "build=${CACHE_BUST}" > /app/BUILD_INFO


# Writable directories for runtime data.
RUN mkdir -p /app/logs /app/data /app/hashes && \
    chown -R vigil:vigil /app/logs /app/data /app/hashes

EXPOSE 8080

USER vigil

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:8080/live || exit 1

CMD ["gunicorn", "vigil.api.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "4", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "65", \
     "--access-logfile", "-"]
