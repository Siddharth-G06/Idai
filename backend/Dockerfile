# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy only the API requirements to leverage Docker cache
COPY requirements.api.txt .

# Install API dependencies cleanly
# This completely bypasses the heavy ML dependencies (PyTorch, FAISS, etc.)
RUN pip install --no-cache-dir -r requirements.api.txt

# Copy the actual source files and the /data directory
COPY . .

# Expose port exactly to prevent Render from dynamically shifting ports and confusing the Cloudflare proxy
EXPOSE 8000

# Start the FastAPI application on the explicit port using EXEC form
# CRITICAL: We must include proxy-headers and forwarded-allow-ips so Uvicorn does not silently drop Cloudflare traffic!
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
