FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create directories for MLOps data
RUN mkdir -p /app/mlops/data /app/mlops/config /app/experiments /app/evaluations /app/model_registry /app/metrics

# Set environment variables
ENV PYTHONPATH=/app
ENV BROWSER_AI_LOGGING_LEVEL=info
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 browserai && chown -R browserai:browserai /app
USER browserai

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import browser_ai; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "mlops.cli", "--help"]