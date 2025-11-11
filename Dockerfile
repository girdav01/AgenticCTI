# AgenticCTI Dockerfile
# Production-ready container for the AgenticCTI platform

FROM python:3.11-slim

# Set metadata
LABEL maintainer="AgenticCTI Team"
LABEL description="Autonomous Cyber Threat Intelligence Platform"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash agentic && \
    chown -R agentic:agentic /app

# Copy requirements first for better caching
COPY --chown=agentic:agentic requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=agentic:agentic . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R agentic:agentic /app/logs /app/data /app/config

# Switch to non-root user
USER agentic

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command (can be overridden)
CMD ["python", "main.py", "schedule"]
