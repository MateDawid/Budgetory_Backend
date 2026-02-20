#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn app_config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --reload --access-logfile - --logger-class app_config.loggers.GunicornLogger

exec "$@"
