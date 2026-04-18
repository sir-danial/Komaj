#!/bin/sh
set -e

echo "[entrypoint] applying migrations..."
python manage.py migrate --noinput

echo "[entrypoint] ensuring cache table exists..."
python manage.py createcachetable || true

echo "[entrypoint] starting: $*"
exec "$@"
