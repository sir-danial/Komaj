#!/bin/sh
set -e

echo "[entrypoint] applying migrations..."
python manage.py migrate --noinput

echo "[entrypoint] ensuring cache table exists..."
python manage.py createcachetable || true

echo "[entrypoint] syncing catalog (idempotent seed)..."
python manage.py seed_catalog || true

echo "[entrypoint] starting: $*"
exec "$@"
