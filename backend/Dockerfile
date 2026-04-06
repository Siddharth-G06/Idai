FROM python:3.11-slim

# Set the working directory (Railway handles the root shift, 
# but inside the container, we usually use /app)
WORKDIR /app

# Copy requirements from your backend folder
COPY requirements.txt .

# Use the -m flag to ensure it finds the pip module
RUN python -m pip install --no-cache-dir -r requirements.txt

    COPY . .

CMD ["python", "main.py"]