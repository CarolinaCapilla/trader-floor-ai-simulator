FROM python:3.12-slim

# Install Node.js for MCP servers (npx)
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all files first (needed for editable install)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Create data directory for persistent DB
RUN mkdir -p /app/data /app/memory

# Set environment variable for DB path
ENV DB_PATH=/app/data/accounts.db

# Railway sets PORT dynamically, no need to expose specific port
# The app will bind to whatever Railway provides via $PORT env var

# Run only the UI - scheduler runs via separate Railway cron or service
# For now, just run the UI so we can verify it works
CMD ["python", "app.py"]
