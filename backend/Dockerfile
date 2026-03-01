FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy from repo root context
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire repo so backend.routers, backend.state etc all resolve
COPY . .

EXPOSE 8000

# Run from repo root so 'backend' module is found
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]