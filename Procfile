web: gunicorn tax_calculator.wsgi --limit-request-line 8188 --log-file -
worker: celery worker --app=tax_calculator --loglevel=info
