release: python manage.py migrate
web: daphne insta_server.asgi:application --port $PORT --bind 0.0.0.0 -v2
worker: python manage.py runworker channels --settings=insta_server.settings -v2