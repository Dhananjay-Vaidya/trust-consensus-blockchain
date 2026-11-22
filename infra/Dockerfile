# Reproducible research environment + dashboard.
#   docker build -f infra/Dockerfile -t trust-consensus .
#   docker run --rm trust-consensus python scripts/reproduce.py --smoke
#   docker run --rm -p 8000:8000 trust-consensus            # API + built dashboard
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONHASHSEED=0
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ make \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
COPY . .
COPY --from=frontend-builder /frontend/dist ./dashboard/dist
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
