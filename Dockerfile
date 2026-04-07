FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

COPY backend/main.py .

# Bypass BuildKit static cache resolution by copying everything and extracting data
COPY . /app_src
RUN cp -r /app_src/data /data || (echo "DATA NOT FOUND! ROOT CONTEXT CONTAINS:" && ls -la /app_src && exit 1)
RUN rm -rf /app_src

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"