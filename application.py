import os
import sys
import traceback

# Add the project root to the Python path.
# This is the directory where application.py is located.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The DJANGO_SETTINGS_MODULE is now correctly set in the .ebextensions/django.config file.
# This ensures a single source of truth for the environment configuration.

# This is the global 'application' variable that Gunicorn/uWSGI will look for.
# We initialize it to None and it will be set in the try/except block.
application = None

try:
    # Import the WSGI application from Django.
    # This will raise an exception if Django is not configured correctly.
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

except Exception as e:
    # If any exception occurs, we'll create a simple error-reporting application.
    # This is crucial for debugging on Elastic Beanstalk as it provides feedback in the browser.
    
    # Log the detailed exception to stderr, which will appear in the Elastic Beanstalk logs.
    print("!!! Django WSGI application failed to load!", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

    # Prepare a detailed HTML response with the error message and traceback.
    # The traceback is formatted for HTML display.
    error_message = str(e)
    error_traceback = traceback.format_exc().replace('\n', '<br>').replace(' ', '&nbsp;')
    
    error_html = f"""
    <html>
    <head>
        <title>Application Error</title>
        <style>
            body {{ font-family: monospace, sans-serif; margin: 2em; background-color: #f8f8f8; }}
            h1 {{ color: #c00; }}
            pre {{ background-color: #333; color: #fff; padding: 1em; border: 1px solid #ccc; overflow-x: auto; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>Application Failed to Start</h1>
        <p>There was an error loading the Django application, which prevents it from starting.</p>
        <p><strong>Error Details:</strong></p>
        <pre>{error_message}</pre>
        <p><strong>Full Traceback:</strong></p>
        <pre>{error_traceback}</pre>
    </body>
    </html>
    """.encode('utf-8')

    # Define a simple WSGI application to return the error page.
    def error_application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html; charset=utf-8'), ('Content-Length', str(len(error_html)))]
        start_response(status, headers)
        return [error_html]

    # Set the global 'application' variable to our error handler.
    application = error_application