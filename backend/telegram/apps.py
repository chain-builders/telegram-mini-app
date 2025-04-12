from django.apps import AppConfig
from .bot import activator


class TelegramConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram'

    def ready(self):
        activator()