# --- Stage 1: front-end assets (Tailwind CSS + self-hosted fonts) ---
FROM node:20-slim AS assets

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Tailwind scans templates + apps for class names (see tailwind.config.js content)
COPY tailwind.config.js ./
COPY static/css/src ./static/css/src
COPY templates ./templates
COPY apps ./apps

# Build the stylesheet, then copy the @fontsource woff/woff2 files next to it so
# the url(files/…) references in output.css resolve (self-hosted fonts).
RUN npm run build:css \
    && mkdir -p static/css/dist/files \
    && cp node_modules/@fontsource-variable/vazirmatn/files/*.woff2 static/css/dist/files/ \
    && cp node_modules/@fontsource/lalezar/files/*.woff* static/css/dist/files/

# --- Stage 2: Python application ---
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Bring in the compiled CSS + fonts from the assets stage (output.css is gitignored).
COPY --from=assets /app/static/css/dist ./static/css/dist

# --ignore=src: don't collect/post-process the Tailwind source (its @import points
# at node_modules and would break the manifest storage).
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /data \
    && python manage.py collectstatic --noinput --ignore=src

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
