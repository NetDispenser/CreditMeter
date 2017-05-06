"""
WSGI config for ev project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os,sys
sys.path.append('/var/www')
sys.path.append('/var/www/meter')
sys.path.append('/var/www/meter/meter')
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meter.settings")

application = get_wsgi_application()
