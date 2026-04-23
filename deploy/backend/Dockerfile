FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy SDK first (backend imports fairlens)
COPY ./sdk ./sdk
RUN pip install -e ./sdk --no-cache-dir

# Copy backend
COPY . .
RUN pip install -r requirements.txt --no-cache-dir

# Copy local database
COPY ./local_data ./local_data

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
