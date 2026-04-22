FROM python:3.10-slim

# Required for AIF360 / LightGBM OpenMP dependency
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /gate

# Install SDK from local source first
COPY ../sdk /sdk
RUN pip install --no-cache-dir /sdk

# Install gate dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy gate code
COPY . .

ENTRYPOINT ["python", "gate.py"]
