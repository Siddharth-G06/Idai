FROM python:3.11-slim

WORKDIR /app

# Copy requirement files from backend directory
COPY backend/requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

# Copy everything from backend to /app
# This includes main.py, .env, and the data/ directory
COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]