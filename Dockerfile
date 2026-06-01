# Serves the Ascension static web app (same layout as Play-Ascension.bat on port 8765).
FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/
COPY cards/ /usr/share/nginx/html/cards/
COPY audio/ /usr/share/nginx/html/audio/

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
