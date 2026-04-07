FROM python:3.11-slim

WORKDIR /app

COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

COPY main.py .
COPY data/ ./data/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]