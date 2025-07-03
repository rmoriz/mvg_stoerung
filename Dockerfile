# Multi-stage Dockerfile for MVG Incident Parser
# Stage 1: Build and test
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy source code
COPY mvg_stoerung.py .
COPY test_*.py ./
COPY run_*.py ./

# Run tests to ensure the build is working
RUN python -m pytest test_mvg_incident_parser.py -v

# Stage 2: Production image
FROM python:3.11-slim as production

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r mvguser && useradd -r -g mvguser mvguser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mvguser/.local

# Copy application files
COPY mvg_stoerung.py .

# Set up PATH for user-installed packages
ENV PATH=/home/mvguser/.local/bin:$PATH

# Change ownership to non-root user
RUN chown -R mvguser:mvguser /app

# Switch to non-root user
USER mvguser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python mvg_stoerung.py > /dev/null 2>&1 || exit 1

# Set default command
ENTRYPOINT ["python", "mvg_stoerung.py"]

# Metadata
LABEL org.opencontainers.image.title="MVG Stoerung"
LABEL org.opencontainers.image.description="Fetches and processes incident data from MVG (Munich Public Transport) API"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="MVG Parser Team"
LABEL org.opencontainers.image.url="https://github.com/rmoriz/mvg_stoerung"
LABEL org.opencontainers.image.source="https://github.com/rmoriz/mvg_stoerung"
LABEL org.opencontainers.image.licenses="CC0-1.0"