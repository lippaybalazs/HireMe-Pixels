#!/bin/sh

set -e

python manage.py migrate
python manage.py initialize_board

exec "$@"