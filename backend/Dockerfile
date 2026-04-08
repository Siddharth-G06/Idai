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

# Start the FastAPI application. Render injects its own $PORT variable dynamically.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
