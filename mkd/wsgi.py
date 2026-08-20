"""
Django WSGI config for mkd project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mkd.settings')

application = get_wsgi_application()
