"""
WSGI config for blog_cheatkey project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Add the project root directory (the one containing the 'backend' folder) to the Python path.
# This ensures that modules like 'backend.accounts' can be imported reliably.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.blog_cheatkey.settings')

application = get_wsgi_application()
