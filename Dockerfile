FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp /app/webapp

ENV AI_DB_CONNECTION_STRING=mongodb://localhost:27017/ai_db

EXPOSE 80

CMD [ "gunicorn", "-w", "4", "-b", ":80", "--timeout", "120", "--worker-class", "gevent", "--worker-connections", "1000", "webapp.run:app" ]
