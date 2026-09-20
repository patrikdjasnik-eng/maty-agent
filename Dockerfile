FROM python:3.13-slim

WORKDIR /app

COPY app ./app
COPY .env.example ./.env.example

RUN useradd --create-home --uid 10001 maty \
  && mkdir -p /app/data /app/reports \
  && chown -R maty:maty /app

USER maty

CMD ["python", "-m", "app.main"]
