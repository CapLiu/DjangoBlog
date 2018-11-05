from django.apps import AppConfig
from django.db.models.signals import post_save

from django.conf import settings




class BlogsearchengineConfig(AppConfig):
    name = 'blogsearchengine'
    def ready(self):
        pass

