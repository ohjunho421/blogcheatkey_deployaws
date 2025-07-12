#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Add the blog_cheatkey directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    blog_cheatkey_path = os.path.join(current_dir, 'blog_cheatkey', 'backend')
    sys.path.insert(0, blog_cheatkey_path)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_cheatkey.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
