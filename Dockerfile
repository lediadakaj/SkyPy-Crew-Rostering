# Production-ready image for the SkyPy Crew Rostering Flask app.
#
# Build:   docker build -t skypy-roster .
# Run:     docker run --rm -p 5000:5000 skypy-roster
# Then:    curl http://localhost:5000/health
#
# We use waitress (pure Python WSGI server) rather than gunicorn so the image
# is cross-platform — the same Dockerfile works on Linux, macOS, and Windows
# Docker hosts. The dev server in app.py is NOT used here.

FROM python:3.12-slim

# Avoid writing .pyc files and force stdout/stderr to flush so container logs
# show up in real time.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only PRODUCTION dependencies (Flask + waitress). Tests, pytest, and
# coverage tooling do not belong in the runtime image. This keeps the layer
# small and the attack surface narrow.
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

# Copy only what's needed to run the service. Tests, README, etc. are
# excluded by .dockerignore.
COPY skypy/ ./skypy/
COPY app.py main.py ./
COPY data/ ./data/

# Run as a non-root user for defence in depth.
RUN useradd --create-home --shell /bin/bash skypy \
    && chown -R skypy:skypy /app
USER skypy

EXPOSE 5000

# Container orchestrators (Kubernetes, Docker Swarm, ECS) use HEALTHCHECK to
# detect crashed-but-not-exited processes. Hits the /health endpoint every 30s.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health').read()" || exit 1

# waitress-serve binds to all interfaces inside the container.
CMD ["waitress-serve", "--listen=0.0.0.0:5000", "app:app"]
