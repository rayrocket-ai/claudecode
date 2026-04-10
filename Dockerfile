FROM python:3.11-slim

WORKDIR /app

COPY requirements-dashboard.txt .
RUN pip install --no-cache-dir -r requirements-dashboard.txt

COPY . .

RUN mkdir -p /app/storage

ENV PORT=8050
EXPOSE 8050

CMD uvicorn dashboard.app:app --host 0.0.0.0 --port ${PORT}
