FROM node:22-bookworm-slim AS web
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 LENS_HOME=/app/runtime
COPY requirements*.txt requirements.lock ./
COPY evaluation/kaggle_olist/requirements.txt evaluation/kaggle_olist/requirements.txt
RUN pip install --no-cache-dir -r evaluation/kaggle_olist/requirements.txt && useradd --uid 10001 --create-home lens && mkdir runtime && chown lens runtime
COPY commerce/ commerce/
COPY evaluation/questions.json evaluation/
COPY --from=web /build/dist frontend/dist
USER lens
EXPOSE 8731
CMD ["sh","-ec","if [ ! -f \"$LENS_HOME/commerce.duckdb\" ]; then python -m commerce.cli demo; fi; exec python -m uvicorn commerce.api:app --host 0.0.0.0 --port 8731"]
