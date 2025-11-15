from django.apps import AppConfig

class QuotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes'

    def ready(self):
        import quotes.signals  # <- this ensures signals.py runs
