FROM python:3.12-slim

# Install Node.js for MCP servers (npx)
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create data directory for persistent DB
RUN mkdir -p /app/data /app/memory

# Set environment variable for DB path
ENV DB_PATH=/app/data/accounts.db

# Expose Gradio port
EXPOSE 7860

# Default command runs both scheduler and UI
# The scheduler runs in background, UI runs in foreground
CMD ["sh", "-c", "python trading_floor.py & python app.py"]
