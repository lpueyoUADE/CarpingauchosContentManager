from django.db.models.signals import post_delete
from django.apps import apps

APP_NAME = 'content'

def auto_register_post_deletes():
    """
    Releva todos los modelos en la app content y registra el on_post_delete.
    """
    app_config = apps.get_app_config(APP_NAME)
    for model in app_config.get_models():
        if hasattr(model, '_on_post_delete'):
            post_delete.connect(
                receiver=model._on_post_delete,
                sender=model,
                weak=False
            )

# Se ejecuta cuando Django carga las apps
auto_register_post_deletes()