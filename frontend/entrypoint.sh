#!/bin/sh

cat > /app/config.js <<EOF
window.API_URL = "${API_URL}";
EOF

exec python -m http.server 8080 --bind 0.0.0.0 --directory /app