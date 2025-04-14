#!/bin/sh
set -e

until pg_isready -h postgres -p 5432 -U roblrash; do
  sleep 2
done

alembic upgrade head

exec gunicorn src.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind REDACTED:8080 \
  --access-logfile -
