# syntax=docker/dockerfile:1
FROM node:20-alpine AS frontend-build
WORKDIR /fe
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund --loglevel=error
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx supervisor \
 && rm -rf /var/lib/nginx/* /var/log/nginx/* /var/lib/apt/lists/* \
 && sed -i 's/^user www-data;/user root;/' /etc/nginx/nginx.conf \
 && mkdir -p /var/lib/nginx/body /var/lib/nginx/proxy /var/lib/nginx/fastcgi \
             /var/lib/nginx/uwsgi /var/lib/nginx/scgi /var/log/nginx
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/ /app/
COPY --from=frontend-build /fe/dist /var/www/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default
COPY supervisord.conf /etc/supervisord.conf
EXPOSE 80 5000
CMD ["supervisord", "-c", "/etc/supervisord.conf", "-n"]
