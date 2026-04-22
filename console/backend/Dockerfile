FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Use main:app (not console.backend.main:app) since Dockerfile COPY puts files at /app/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
