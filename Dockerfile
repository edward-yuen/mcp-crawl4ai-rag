FROM python:3.12-slim

ARG PORT=8051

WORKDIR /app

# Install uv
RUN pip install uv

# Copy the MCP server files
COPY . .

# Install packages directly to the system (no virtual environment)
# Combining commands to reduce Docker layers
RUN uv pip install --system -e . && \
    crawl4ai-setup

# Conditionally expose port only if using SSE transport
EXPOSE ${PORT}

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Command to run the MCP server
# The server will automatically detect transport mode from environment variables
CMD ["python", "src/crawl4ai_mcp.py"]