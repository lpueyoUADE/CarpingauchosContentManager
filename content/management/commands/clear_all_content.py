from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Elimina todos los datos de los modelos en la app "content".'

    def handle(self, *args, **kwargs):
        app_models = apps.get_app_config('content').get_models()
        for model in app_models:
            model_name = model.__name__
            self.stdout.write(f"Eliminando todos los objetos de {model_name}")
            model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Todos los datos fueron eliminados.'))