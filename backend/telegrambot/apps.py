from django.apps import AppConfig
from .bot import TelegramBot

class TelegrambotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegrambot'

    def ready(self):
        bot_instance = TelegramBot()
        bot_instance.initialize_web3_connections()
        bot_instance.setup_app()
