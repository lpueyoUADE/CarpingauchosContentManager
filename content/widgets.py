import os
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

DEFAULT_PREFAB_IMAGE = "/static/admin/images/default_prefab.png" 

#TODO: Revisar esto porque se cambia solo el icono seleccionado
def _get_file_choices(files_base_path, *valid_file_formats):
    base_path = files_base_path
    if not base_path or not os.path.exists(base_path):
        return []

    choices = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(valid_file_formats):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_path)
                choices.append((full_path, rel_path))  # value = ruta absoluta, label = ruta relativa

    return sorted(choices, key=lambda x: x[1])

def get_sprite_choices():
    return _get_file_choices(settings.SPRITES_BASE_PATH, '.png')

def get_prefab_choices():
    return _get_file_choices(settings.PREFABS_BASE_PATH, '.prefab')

class FileGridWidget(forms.Select):
    static_files_path = ''
    template_name = 'widgets/file_grid.html'
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        options = []
        for group_name, group_choices, index in context['widget']['optgroups']:
            for option in group_choices:
                abs_path = option['value']
                rel_path = option['label']
                img_url = f"/{self.static_files_path}/{rel_path}".replace('\\', '/')
                
                # Para archivos .prefab, usar imagen por defecto
                if rel_path.endswith('.prefab'):
                    img_url = DEFAULT_PREFAB_IMAGE
                else:
                    img_url = f"/{self.static_files_path}/{rel_path}".replace('\\', '/')

                options.append({
                    'value': abs_path, #TODO: Arreglar que el path no incluya lo previo a Assets/_develop etc.
                    'label': os.path.basename(rel_path),
                    'selected': option['value'] == value,
                    'image_url': img_url
                })
        context['options'] = options
        context['file_type'] = self.selected_title
        return context
    
class SpriteGridWidget(FileGridWidget):
    static_files_path = 'static_sprites'
    selected_title = 'sprites'

class PrefabGridWidget(FileGridWidget):
    static_files_path = 'static_prefabs'
    selected_title = 'prefabs'