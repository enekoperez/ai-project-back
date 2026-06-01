FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp /app/webapp

# ENV FLASK_APP=run.py
# ENV FLASK_ENV=production

EXPOSE 80

# CMD [ "gunicorn", "-w", "4", "-b", ":80", "--timeout", "120", "--worker-class", "gevent", "--worker-connections", "1000", "webapp.run:app" ]
CMD ["python", "-m", "webapp.run"]
