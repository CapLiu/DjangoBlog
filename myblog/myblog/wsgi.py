#!/usr/bin/python3.5
"""
WSGI config for myblog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
from os.path import join,dirname,abspath
import sys
sys.path.append('/home/liu/.local/lib/python3.5/site-packages')
# sys.path.append('/usr/local/lib/python3.5/dist-packages')
# print(sys.path)
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myblog.settings")

application = get_wsgi_application()
