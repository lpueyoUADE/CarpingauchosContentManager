import os
from django import forms
from django.conf import settings

DEFAULT_PREFAB_IMAGE = "/static/admin/images/default_prefab.png" 
EMPTY_IMAGE = "/static/admin/images/empty.png"

def _get_file_choices(partial_base_path, *valid_file_formats):
    base_path = settings.ABSOLUTE_BASE_PATH + partial_base_path
    if not base_path or not os.path.exists(base_path):
        return []

    choices = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(valid_file_formats):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
                unity_path = (partial_base_path + rel_path).replace("\\", "/")
                choices.append((unity_path, rel_path))

    # Opción vacia siempre como primer item
    return [("", "Ninguno")] + sorted(choices, key=lambda x: x[1])

def get_sprite_choices():
    return _get_file_choices(settings.SPRITES_BASE_PATH, '.png')

def get_prefab_choices():
    return _get_file_choices(settings.PREFABS_BASE_PATH, '.prefab')

class FileGridWidget(forms.Select):
    static_files_path = ''
    files_partial_base_path = ''
    template_name = 'widgets/file_grid.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        options = []

        for group_name, group_choices, index in context['widget']['optgroups']:
            for option in group_choices:
                unity_path = option['value']
                rel_path = option['label']
                img_url = f"/{self.static_files_path}/{rel_path}".replace('\\', '/')
                
                # Para archivos .prefab, usar imagen por defecto
                if rel_path.endswith('.prefab'):
                    img_url = DEFAULT_PREFAB_IMAGE
                
                elif rel_path == 'Ninguno':
                    img_url = EMPTY_IMAGE
                else:
                    img_url = f"/{self.static_files_path}/{rel_path}".replace('\\', '/')

                options.append({
                    'value': unity_path.replace("\\", "/"),
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
    files_partial_base_path = settings.SPRITES_BASE_PATH

class PrefabGridWidget(FileGridWidget):
    static_files_path = 'static_prefabs'
    selected_title = 'prefabs'
    files_partial_base_path = settings.PREFABS_BASE_PATH