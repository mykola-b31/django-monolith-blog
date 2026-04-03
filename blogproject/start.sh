#!/bin/bash
echo "Waiting for postgres..."
until nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"
python manage.py migrate
echo "Migration finished"
python manage.py createsuperuser --noinput
echo "Superuser created"
python manage.py runserver 0.0.0.0:8000
echo "Server started"