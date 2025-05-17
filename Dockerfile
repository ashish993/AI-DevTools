# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set build arguments and environment variables
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies and clean up in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    graphviz \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Create application user
RUN useradd -m -r appuser && \
    chown -R appuser:appuser /app

# Create necessary directories and set permissions
RUN mkdir -p temp static templates diagrams .streamlit && \
    chown -R appuser:appuser /app/*

# Copy and install requirements first (better layer caching)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and assets with correct permissions
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser diagrams/ ./diagrams/
COPY --chown=appuser:appuser .streamlit/ ./.streamlit/
COPY --chown=appuser:appuser temp/ ./temp/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose the port Streamlit runs on
EXPOSE 8501

# Set the entrypoint script
CMD ["streamlit", "run", "src/app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501", \
     "--browser.serverAddress", "0.0.0.0", \
     "--server.maxUploadSize", "200"]