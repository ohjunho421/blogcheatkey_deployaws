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

# Add the blog_cheatkey/backend directory to Python path
current_dir = Path(__file__).resolve().parent
blog_cheatkey_backend_path = current_dir / 'blog_cheatkey' / 'backend'
sys.path.insert(0, str(blog_cheatkey_backend_path))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_cheatkey.settings')

application = get_wsgi_application()
