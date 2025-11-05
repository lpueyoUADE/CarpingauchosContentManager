import csv
from django import forms
from django.contrib import admin, messages
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, OneToOneField, ForeignKey, FloatField, CASCADE
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect, HttpResponse
from django.core.serializers import serialize
from django.conf import settings
from .widgets import get_sprite_choices, get_prefab_choices, SpriteGridWidget, PrefabGridWidget
from .models import (
    Localization,
    NPC,
    Quest, 
    QuestObjective,
    ItemAttributes,
    ItemReward,
    Item, 
    Consumable,
    Weapon, 
    Equipment, 
    Rarity, 
    QuestItem, 
    WeaponType, 
    DamageType,
    EquipmentType,
    AttackSequence,
    WeaponAttackSequence,
    LoadingScreenMessage,
    POI,
    Projectile,
    ProjectileType,
    AbilityTree,
    Ability,
    AbilityType,
    Condition,
    Dialogue,
    Basic,
    QuestPrompt,
    QuestEnd,
    DialogueSequence,
    DialogueSingleItem,
    DialogueSequenceItem,
    DialogItemsRequired,
    DialogItemsToRemove,
    DialogItemsToGive,
    DiaryPage,
    DiaryEntry,
    )

from io import StringIO
import json
import os
from datetime import datetime

class CustomAdminSite(admin.AdminSite):
    site_header = "Carpingauchos Content Manager"
    index_title = "App para gestión de contenido"
    
    def get_app_list(self, request, app_label=None):
        """
        Order custom para los modelos.
        """
        app_list = super().get_app_list(request)
        for app in app_list:
            app['models'].sort(key=lambda model: int(model['name'].split('.')[0]) if model['name'].split('.')[0].isdigit() else 999)
        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("export-localization/", self.admin_view(self.export_localization), name="export-localization"),
            path("download-full-json/", self.admin_view(self.download_full_json), name="download-full-json"),
            path("download-quests/", self.admin_view(self.download_quests), name="download-quests"),
            path("download-diary-pages/", self.admin_view(self.download_diary_pages), name="download-diary-pages"),
            path("download-dialogues/", self.admin_view(self.download_dialogues), name="download-dialogues"),
            path("download-items/", self.admin_view(self.download_items), name="download-items"),
            path("download-localizations/", self.admin_view(self.download_localizations), name="download-localizations"),
        ]
        return custom_urls + urls

    def export_localization(self, request):
        # Serializamos Localization
        data = serialize('json', Localization.objects.all(), indent=4)
        export_path = os.path.join(settings.BASE_DIR, 'exports', 'localization.json')
        os.makedirs(os.path.dirname(export_path), exist_ok=True)

        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(data)

        messages.success(request, "Localization exportado correctamente.")
        return HttpResponseRedirect("/admin/")
    
    def download_full_json(self, request):
        buffer = StringIO()

        # Serializamos múltiples modelos y los agregamos al buffer como una lista JSON
        data = {
            'Rarity': Rarity.to_dict(),
            'WeaponType': WeaponType.to_dict(),
            'EquipmentType': EquipmentType.to_dict(),
            'ProjectileType': ProjectileType.to_dict(),
            'AbilityType': AbilityType.to_dict(),
            'Localization': Localization.to_dict(),
            'Item': {
                'Weapon': Item.to_dict(Weapon),
                'Equipment': Item.to_dict(Equipment),
                'Consumable': Item.to_dict(Consumable),
                'Quest': Item.to_dict(QuestItem),
            },
            'Quest': Quest.to_dict(),
            'QuestObjective': QuestObjective.to_dict(),
            'LoadingScreenMessage': LoadingScreenMessage.to_dict(),
            'POI': POI.to_dict(),
            'AbilityTree': AbilityTree.to_dict(),
            'Ability':Ability.to_dict(),
            'Projectile': Projectile.to_dict(),
            'NPC': NPC.to_dict(),
            'Dialogue': 
                Dialogue.to_dict(Basic) +
                Dialogue.to_dict(QuestPrompt) +
                Dialogue.to_dict(QuestEnd)
            ,
            'DiaryPage': DiaryPage.to_dict(),
            'DiaryEntry': DiaryEntry.to_dict(),
            'Condition':Condition.to_dict(),
        }

        # Convertimos a JSON final
        json.dump(data, buffer, indent=4, ensure_ascii=False)

        today = datetime.now().strftime("%d-%m-%Y")
        filename = f"full_export_{today}.json"

        response = HttpResponse(buffer.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, "Exportación completa generada y descargada.")
        return response

    def donwload_template(self, request, model, exported_model_name):
        buffer = StringIO()
        data =model.to_dict2()

        # Convertimos a JSON final
        json.dump(data, buffer, indent=4, ensure_ascii=False)

        today = datetime.now().strftime("%d-%m-%Y")
        filename = f"{exported_model_name.lower()}_export_{today}.json"

        response = HttpResponse(buffer.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, f"JSON de {exported_model_name.replace('_', ' ')}s generado con éxito.")
        return response

    def download_quests(self, request):
        return self.donwload_template(request, Quest, "Quest")

    def download_diary_pages(self, request):
        return self.donwload_template(request, DiaryPage, "Diary_Page")

    def download_dialogues(self, request):
        return self.donwload_template(request, Dialogue, "Dialogue")
    
    def download_items(self, request):
        return self.donwload_template(request, Item, "Item")
    
    def download_localizations(self, request):
        # Obtener queryset con TODOS los registros
        queryset = Localization.objects.all()

        # Podés pasar None o self si querés como modeladmin
        #return export_all_csv(None, request, queryset)

        return export_all_json(None, request, queryset)

custom_admin_site = CustomAdminSite(name='custom_admin')

def _add_localization_field_filter(key_prefix, db_field, kwargs):
    """
    Filtro para los campos de Tipo Localization.
    Solo muestra los locs. del mismo prefijo que el modelo a cargar.
    """
    if db_field.related_model == Localization:
        # Filtramos por key que contenga cierto texto
        kwargs["queryset"] = Localization.objects.filter(Q(key__icontains=key_prefix) & Q(key__icontains=db_field.name)).order_by('key')

class AutoKeyMixin(admin.ModelAdmin):
    class Media:
        js = ('admin/js/auto_key.js',)

class BaseModelAdmin(admin.ModelAdmin):
    key_prefix = ''

    class Media:
        css = {
            'all': (
                'admin/css/custom_admin_filter_sidebar.css',
                'admin/css/custom_admin_submit_row.css',
                'admin/css/custom_admin_identifier_column.css',
            )
        }
        js = (
            'admin/js/get_sanitized_key.js',
            'admin/js/auto_localizations.js',
            'admin/js/file_grid.js'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.key_prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Seteo del prefijo para luego autogenerar los keys.
        """
        form = super().get_form(request, obj, **kwargs)
        prefix = self.key_prefix
        form.base_fields['identifier'].widget.attrs['data-key-prefix'] = prefix
        return form
    
    def get_changeform_initial_data(self, request):
        """
        Seteo del identifier para los popups.
        """
        initial = super().get_changeform_initial_data(request)
        if 'identifier' in request.GET:
            initial['identifier'] = request.GET['identifier']
        return initial
    
    def get_localizations_to_delete(self, obj, seen=None):
        """
        Devuelve todas las localizations asociadas al objeto y a sus hijos
        relacionados por FK con on_delete=CASCADE.
        """

        if seen is None:
            seen = set()

        if obj in seen:
            return []
        seen.add(obj)

        localizations = []

        for field in obj._meta.get_fields():
            # Revisar si este objeto tiene un OneToOne a Localization
            if isinstance(field, OneToOneField) and field.related_model == Localization:
                loc = getattr(obj, field.name)
                if loc:
                    localizations.append(loc)

            # Solo relaciones inversas con FK y on_delete=CASCADE
            if field.is_relation and field.auto_created and not field.concrete:
                related_model = field.related_model
                fk_field = field.field  # El campo FK real en el modelo hijo
                if isinstance(fk_field, ForeignKey) and fk_field.remote_field.on_delete == CASCADE:
                    # Buscar hijos que referencien a este obj
                    related_objs = related_model.objects.filter(**{fk_field.name: obj})
                    for child in related_objs:
                        localizations.extend(self.get_localizations_to_delete(child, seen))

        return localizations


    def get_deleted_objects(self, objs, request):
        """
        Summary list del borrado manual de las localizations, objetos relacionados y sus locs respectivos.
        """
        # Llamamos a la implementación original para que arme el borrado normal
        deletions, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)

        for obj in objs:
            for loc in self.get_localizations_to_delete(obj):
                if loc not in deletions:
                    deletions.append(loc)
                    model_count[Localization._meta.verbose_name] = model_count.get(Localization._meta.verbose_name, 0) + 1

        return deletions, model_count, perms_needed, protected

def _add_validators_to_numeric_fields(self):
    """
    Agrega los maximos y minimos definidos en el modelo para los campos float.
    """
    for field_name, field in self.fields.items():
        model_field = self._meta.model._meta.get_field(field_name)
        
        if not isinstance(model_field, models.FloatField) and \
            not isinstance(model_field, models.IntegerField) and \
            not isinstance(model_field, models.PositiveIntegerField):
            continue

        min_val = None
        max_val = None

        for validator in model_field.validators:
            if isinstance(validator, MinValueValidator):
                min_val = validator.limit_value
            elif isinstance(validator, MaxValueValidator):
                max_val = validator.limit_value

        if min_val is not None:
            field.widget.attrs['min'] = min_val
        if max_val is not None:
            field.widget.attrs['max'] = max_val

        # Texto de ayuda automático
        if min_val is not None and max_val is not None:
            field.help_text = f"Valor entre {min_val} y {max_val}"
        elif min_val is not None:
            field.help_text = f"Valor mínimo: {min_val}"
        elif max_val is not None:
            field.help_text = f"Valor máximo: {max_val}"


class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _add_validators_to_numeric_fields(self)

        # Autocompletado de la key
        self.fields['key'].widget.attrs['readonly'] = True
        self.fields['identifier'].widget.attrs['data-key-prefix'] = self._meta.model.prefix

        # Para usar SpriteGridWidget en cualquier modelo que tenga un campo 'icon_path'
        if 'icon_path' in self.fields:
            self.fields['icon_path'] = forms.ChoiceField(
                choices=get_sprite_choices(),
                widget=SpriteGridWidget()
            )

        if 'locked_icon_path' in self.fields:
            self.fields['locked_icon_path'] = forms.ChoiceField(
                choices=get_sprite_choices(),
                widget=SpriteGridWidget()
            )

        if 'unlocked_icon_path' in self.fields:
            self.fields['unlocked_icon_path'] = forms.ChoiceField(
                choices=get_sprite_choices(),
                widget=SpriteGridWidget()
            )

        # Para usar PrefabGridWidget en cualquier modelo que tenga un campo 'prefab'
        if 'prefab' in self.fields:
            self.fields['prefab'] = forms.ChoiceField(
                choices=get_prefab_choices(),
                widget=PrefabGridWidget(),
            )

        if 'mesh_path' in self.fields:
            self.fields['mesh_path'] = forms.ChoiceField(
                choices=get_prefab_choices(),
                widget=PrefabGridWidget(),
                required=False,
            )

    class Meta:
        widgets = {
            'identifier': forms.TextInput(
                attrs={
                    'placeholder': 'Nombre descriptivo de la entidad (no repetible)',
                    'style': 'width: 50%;',
                }
            ),
            'key': forms.TextInput(
                attrs={
                    'placeholder': 'Identificador único del recurso auto generado',
                    'style': 'width: 50%;',
                    'readonly': True,
                }
            ),
        }

class LocalizationForm(BaseModelForm):
    key_prefix = Localization.prefix

    class Meta(BaseModelForm.Meta):
        model = Localization
        fields = '__all__'
        readonly_fields = ('identifier',)
        widgets = {
            'identifier': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
            'key': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
        }  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si tengo instance y instance pk estoy editando, en ese caso readonly = false.
        readonly = not self.instance or not self.instance.pk 

        self.fields['key'].widget.attrs['readonly'] = readonly
        self.fields['identifier'].widget.attrs['readonly'] = readonly
        self.fields['identifier'].widget.attrs['data-key-prefix'] = self.key_prefix

class ModelNameFilter(admin.SimpleListFilter):
    title = "Model"
    parameter_name = "model_name"
    model_admin = None

    def lookups(self, request, model_admin):
        # Obtener valores únicos de model_name dinámicamente
        self.model_admin = model_admin
        qs = model_admin.get_queryset(request)
        values = set()
        for obj in qs:
            instance = model_admin.get_related_instance(obj)
            if instance:
                values.add(instance._meta.model_name)
        return [(v, v.capitalize()) for v in sorted(values)]

    def queryset(self, request, queryset):
        if self.value():
            # Filtrar queryset por el model_name elegido
            ids = []
            for obj in queryset:
                instance = self.model_admin.get_related_instance(obj)
                if instance and instance._meta.model_name == self.value():
                    ids.append(obj.id)
            return queryset.filter(id__in=ids)
        return queryset

def export_csv(modeladmin, request, queryset):
    """
    Exporta a CSV respetando filtros + selección.
    """

    # Esto es por si al filtrar, selecciono modelos de más de un modelo.
    # se va a notar porque el nombre va incluir todos los model_names.
    # Normalmente deberia ser 1 solo.
    model_names_set = set()

    for obj in queryset:
        instance = modeladmin.get_related_instance(obj)
        if instance:
            model_names_set.add(instance._meta.model_name)

    # Convertimos el set en string con "_"
    model_names = "_".join(sorted(model_names_set))

    # Obtener lo que se escribió en la barra de búsqueda
    search_text = request.GET.get("q", "").strip()

    # Sanitizar para que sea válido como nombre de archivo
    import re
    if search_text:
        safe_search_text = re.sub(r'[^a-zA-Z0-9_-]+', "_", search_text)
        filename = f"Localizations_{model_names}s_{safe_search_text}.csv"
    else:
        filename = f"Localizations_{model_names}s.csv"

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Headers
    writer.writerow(['Key', 'English(en)', 'Spanish(es)'])

    for  obj in queryset:
        writer.writerow([obj.key, obj.english, obj.spanish])

    return response

supported_loc_tables = [
    {
        'localization_id': 'Chapters',
        'models': [
            'loc_diarypage_',
            'loc_diaryentry_',
        ],
    },
    {
        'localization_id': 'Dialogues',
        'models': [
            'loc_dialogue_',
            'loc_dialoguesequenceitem_',
            'loc_dialoguesingleitem_',
        ],
    },
    {
        'localization_id': 'Items_Armor',
        'models': ['loc_item_equipment_'],
    },
    {
        'localization_id': 'Items_Consumables',
        'models': ['loc_item_consumable_'],
    },
    {
        'localization_id': 'Items_Key',
        'models': ['loc_item_quest_item_'],
    },
    {
        'localization_id': 'Items_Weapons',
        'models': ['loc_item_weapon_'],
    },
    {
        'localization_id': 'NPCs',
        'models': ['loc_npc_'],
    },
    {
        'localization_id': 'Quests',
        'models': [
            'loc_quest_',
            'loc_questobjective_',
        ],
    },
]

def export_all_json(modeladmin, request, queryset):
    def get_table_from_key(key: str):
        key_lower = key.lower()
        for table in supported_loc_tables:
            for prefix in table['models']:
                if key_lower.startswith(prefix):
                    return table['localization_id']
        return None  # ignorar entradas sin match

    # Generar nombre de archivo con fecha
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"Localizations_All_{date_str}.json"

    data = []

    for obj in queryset:
        table = get_table_from_key(obj.key)
        if table is None:
            continue  # ignorar entradas sin match

        data.append({
            "Key": obj.key,
            "English": getattr(obj, 'english', ''),
            "Spanish": getattr(obj, 'spanish', ''),
            "Table": table
        })

    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(json.dumps({"entries": data}, ensure_ascii=False, indent=2))
    return response

def export_all_csv(modeladmin, request, queryset):
    def get_table_from_key(key: str):
        key_lower = key.lower()
        for table in supported_loc_tables:
            for prefix in table['models']:
                if key_lower.startswith(prefix):
                    return table['localization_id']
        return None  # ignorar entradas sin match

    # Generar nombre de archivo con fecha
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"Localizations_All_{date_str}.csv"

    # Generar respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Key', 'English(en)', 'Spanish(es)', 'Table'])

    for obj in queryset:
        table = get_table_from_key(obj.key)
        if table is None:
            continue  # ignorar entradas sin match

        writer.writerow([
            obj.key,
            getattr(obj, 'english', ''),
            getattr(obj, 'spanish', ''),
            table
        ])

    return response

export_csv.short_description = "Exportar selección a CSV"
export_all_csv.short_description = "Exportar todo a CSV"
@admin.register(Localization, site=custom_admin_site)
class LocalizationAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = Localization.prefix

    list_display = ('identifier', 'key', 'model_name', 'english', 'spanish')
    ordering = ('key',)
    list_filter = (ModelNameFilter,)
    search_fields = ('identifier', 'english', 'spanish')
    actions = [export_csv, export_all_csv] 

    form = LocalizationForm

    def get_related_instance(self, obj):
        """
        Devuelve la instancia del modelo que tiene OneToOne con este C
        (el que exista).
        """
        for rel in obj._meta.related_objects:
            related_name = rel.get_accessor_name()
            try:
                instance = getattr(obj, related_name)
                return instance
            except rel.related_model.DoesNotExist:
                continue
        return None

    def model_name(self, obj):
        instance = self.get_related_instance(obj)
        if instance:
            return instance._meta.model_name
        return None

    model_name.short_description = "Model"


class QuestObjectiveForm(BaseModelForm):
    key_prefix = QuestObjective.prefix

    class Meta(BaseModelForm.Meta):
        model = QuestObjective
        fields = '__all__'

class QuestObjectiveInline(admin.TabularInline):
    model = QuestObjective
    form = QuestObjectiveForm

    extra = 1  # cuántos formularios vacíos mostrar para crear nuevos objetivos

    class Media:
        js = (
            'admin/js/get_sanitized_key.js',
            'admin/js/auto_key_inline.js',
            'admin/js/tabularinline_questobjectives_index_autoincrement.js',
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(QuestObjective, site=custom_admin_site)
class QuestObjectiveAdmin(BaseModelAdmin, AutoKeyMixin):
    list_display = ('identifier', 'key', 'quest_identifier','english_name', 'spanish_name',)

    ordering = ('key',)

    form = QuestObjectiveForm

    def has_add_permission(self, request):
        can_add_quest_objectives = (
            'content_quest_add'
        )
        return request.resolver_match and request.resolver_match.url_name in can_add_quest_objectives
    
    def english_name(self, obj):
        return obj.brief.english
    english_name.short_description = "Brief (EN)"

    def spanish_name(self, obj):
        return obj.brief.spanish
    spanish_name.short_description = "Brief (ES)"

    def quest_identifier(self, obj):
        return obj.quest.identifier
    quest_identifier.short_description = "Quest"

class QuestForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Quest
        fields = '__all__'

@admin.register(NPC, site=custom_admin_site)
class NPCAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = NPC.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "Name (EN)"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "Name (ES)"

class ItemRewardInline(admin.TabularInline):
    model = ItemReward
    extra = 1

@admin.register(Quest, site=custom_admin_site)
class QuestAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = Quest.prefix

    inlines = [QuestObjectiveInline, ItemRewardInline]
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    ordering = ('key',)

    form = QuestForm
      
    def english_name(self, obj):
        return obj.title.english
    english_name.short_description = "Title (EN)"

    def spanish_name(self, obj):
        return obj.title.spanish
    spanish_name.short_description = "Title (ES)"

class BaseItemInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _add_validators_to_numeric_fields(self)

        # Para usar SpriteGridWidget en cualquier modelo que tenga un campo 'icon_path'
        if 'icon_path' in self.fields:
            self.fields['icon_path'] = forms.ChoiceField(
                choices=get_sprite_choices(),
                widget=SpriteGridWidget()
            )

        # Para usar PrefabGridWidget en cualquier modelo que tenga un campo 'prefab'
        if 'prefab' in self.fields:
            self.fields['prefab'] = forms.ChoiceField(
                choices=get_prefab_choices(),
                widget=PrefabGridWidget(),
            )
        
        if 'mesh_path' in self.fields:
            self.fields['mesh_path'] = forms.ChoiceField(
                choices=get_prefab_choices(),
                widget=PrefabGridWidget(),
                required=False,
            )

    def has_changed(self):
        """ Should returns True if data differs from initial. 
        By always returning true even unchanged inlines will get validated and saved."""
        return True

class ConsumableInlineForm(BaseItemInlineForm):
    class Meta:
        model = Consumable
        fields = '__all__'

class WeaponInlineForm(BaseItemInlineForm):
    class Meta:
        model = Weapon
        fields = '__all__'

class EquipmentInlineForm(BaseItemInlineForm):
    class Meta:
        model = Equipment
        fields = '__all__'

class QuestItemInlineForm(BaseItemInlineForm):
    class Meta:
        model = QuestItem
        fields = '__all__'

class ItemAttributesInlineForm(BaseItemInlineForm):
    class Meta:
        model = ItemAttributes
        fields = '__all__'

class ConsumableInline(admin.StackedInline):
    model = Consumable
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = ConsumableInlineForm

class WeaponInline(admin.StackedInline):
    model = Weapon
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = WeaponInlineForm

class EquipmentInline(admin.StackedInline):
    model = Equipment
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = EquipmentInlineForm

class QuestItemInline(admin.StackedInline):
    model = QuestItem
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = QuestItemInlineForm

class ItemAttributesInline(admin.StackedInline):
    model = ItemAttributes
    extra = 1
    min_num = 1
    max_num = 1
    can_delete = False

    form = ItemAttributesInlineForm

class ItemForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Item
        fields = ('identifier', 'key', 'rarity', 'type', 'name', 'description', 'value', 'icon_path', 'mesh_path')

    def has_changed(self):
        return True

@admin.register(WeaponType, site=custom_admin_site)
class WeaponTypeAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = WeaponType.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)
        
    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

# @admin.register(DamageType, site=custom_admin_site)
# class DamageTypeAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = DamageType.prefix
#     list_display = ('identifier', 'key', 'damage_type_id', 'english_name', 'spanish_name',)
#     ordering = ('damage_type_id',)
   
#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

# @admin.register(EquipmentType, site=custom_admin_site)
# class EquipmentTypeAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = EquipmentType.prefix
#     list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
#     ordering = ('key',)

#     def has_add_permission(self, request, obj=None):
#         enabled_views = (
#             'index',
#             'content_equipment_type_changelist',
#             'content_equipment_type_add',
#             'content_equipment_type_change'
#         )
#         return request.resolver_match and request.resolver_match.url_name in enabled_views
     
#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

class AttackSequenceForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = AttackSequence
        fields = '__all__'

@admin.register(AttackSequence, site=custom_admin_site)
class AttackSequenceAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = AttackSequence.prefix

    list_display = ('identifier', 'key',)
    ordering = ('key',)
    form = AttackSequenceForm

@admin.register(Item, site=custom_admin_site)
class ItemAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = Item.prefix
    list_display = ('identifier', 'key', 'type', 'rarity_name', 'value', 'english_name', 'spanish_name',
                    'flat_physical_damage', 'flat_magical_damage',
                    'armor_physical_resistance', 'armor_magical_resistance',
                    'cooldown', 'duration',
                    'cost_health', 'cost_mana', 'cost_stamina',
                    'give_health', 'give_mana', 'give_stamina', 
                    'buff_health_percent', 'buff_mana_percent', 'buff_stamina_percent', 'buff_physical_damage_percent', 
                    'buff_magical_damage_percent', 'buff_stamina_regeneration_percent', 
                    'nerf_physical_damage_percent', 'nerf_magical_damage_percent', 
                    'nerf_extra_physical_damage_received_percent', 'nerf_extra_magical_damage_received_percent',)
    ordering = ('key', 'type')
    list_filter = ("type",) 
    inlines = [
        WeaponInline, EquipmentInline, ConsumableInline, QuestItemInline, ItemAttributesInline,
    ]

    form = ItemForm

    class Media:
        css = {
            'all':('admin/css/custom_admin_itemattributes_table.css',),
        }
        js = (
            'admin/js/item_auto_key.js', 
            'admin/js/item_type_toggle.js'
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # si ya existe, es edición
            return ['type']
        return []

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"
    
    def rarity_name(self, obj):
        return format_html(
                '<span style="color: {};">{}</span>',
                obj.rarity.color_start,
                obj.rarity.name.english 
            )
    rarity_name.short_description = "Rarity"
    rarity_name.admin_order_field = 'rarity'

    # Items
    def flat_physical_damage(self, obj):
        value = obj.itemattributes_item.flat_physical_damage
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def flat_magical_damage(self, obj):
        value = obj.itemattributes_item.flat_magical_damage
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def armor_physical_resistance(self, obj):
        value = obj.itemattributes_item.armor_physical_resistance
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def armor_magical_resistance(self, obj):
        value = obj.itemattributes_item.armor_magical_resistance
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    # Timing
    def cooldown(self, obj):
        value = obj.itemattributes_item.cooldown
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def duration(self, obj):
        value = obj.itemattributes_item.duration
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    # Costs
    def cost_health(self, obj):
        value = obj.itemattributes_item.cost_health
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def cost_mana(self, obj):
        value = obj.itemattributes_item.cost_mana
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def cost_stamina(self, obj):
        value = obj.itemattributes_item.cost_stamina
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    # Gives
    def give_health(self, obj):
        value = obj.itemattributes_item.give_health
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def give_mana(self, obj):
        value = obj.itemattributes_item.give_mana
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def give_stamina(self, obj):
        value = obj.itemattributes_item.give_stamina
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    # Buffs
    def buff_health_percent(self, obj):
        value = obj.itemattributes_item.buff_health_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def buff_mana_percent(self, obj):
        value = obj.itemattributes_item.buff_mana_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def buff_stamina_percent(self, obj):
        value = obj.itemattributes_item.buff_stamina_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def buff_physical_damage_percent(self, obj):
        value = obj.itemattributes_item.buff_physical_damage_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def buff_magical_damage_percent(self, obj):
        value = obj.itemattributes_item.buff_magical_damage_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def buff_stamina_regeneration_percent(self, obj):
        value = obj.itemattributes_item.buff_stamina_regeneration_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    # Nerfs
    def nerf_physical_damage_percent(self, obj):
        value = obj.itemattributes_item.nerf_physical_damage_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def nerf_magical_damage_percent(self, obj):
        value = obj.itemattributes_item.nerf_magical_damage_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def nerf_extra_physical_damage_received_percent(self, obj):
        value = obj.itemattributes_item.nerf_extra_physical_damage_received_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )

    def nerf_extra_magical_damage_received_percent(self, obj):
        value = obj.itemattributes_item.nerf_extra_magical_damage_received_percent
        return format_html(
            '<span style="color: {};">{}</span>',
            '#0F0' if value != 0 else 'initial',
            value
        )



class RarityForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Rarity
        fields = '__all__'
        widgets = {
            'color_start': forms.TextInput(attrs={'type': 'color'}),
            'color_end': forms.TextInput(attrs={'type': 'color'}),
        }

# @admin.register(Rarity, site=custom_admin_site)
# class RarityAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = Rarity.prefix
#     list_display = ('key', 'rarity_json_id','gradient_color_start', 'gradient_color_end', 'rarity_name','english_name', 'spanish_name',)

#     ordering = ('rarity_json_id',)

#     form = RarityForm

#     def has_add_permission(self, request, obj=None):
#         enabled_views = (
#             'index',
#             'content_rarity_changelist',
#             'content_rarity_add',
#             'content_rarity_change'
#         )
#         return request.resolver_match and request.resolver_match.url_name in enabled_views
    
#     def has_delete_permission(self, request, obj=None):
#         enabled_views = (
#             'index',
#             'content_rarity_changelist',
#             'content_rarity_add',
#             'content_rarity_change'
#         )
#         return request.resolver_match and request.resolver_match.url_name in enabled_views
    
#     def has_change_permission(self, request, obj=None):
#         enabled_views = (
#             'index',
#             'content_rarity_changelist',
#             'content_rarity_add',
#             'content_rarity_change'
#         )
#         return request.resolver_match and request.resolver_match.url_name in enabled_views
    

#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"
  
#     def gradient_color_start(self, obj):
#         return format_html(
#             '<span style="color: {};">{}</span>',
#             obj.color_start,
#             obj.color_start
#         )
    
#     gradient_color_start.short_description = "Color Start"
    
#     def gradient_color_end(self, obj):
#         return format_html(
#             '<span style="color: {};">{}</span>',
#             obj.color_end,
#             obj.color_end 
#         )
    
#     gradient_color_end.short_description = "Color End"

#     def rarity_name(self, obj):
#         return format_html(
#             '<span style="color: {};">{}</span>',
#             obj.color_start,
#             obj.name.english 
#         )

#     rarity_name.short_description = "Name"
#     rarity_name.admin_order_field = 'name'


# @admin.register(LoadingScreenMessage, site=custom_admin_site)
# class LoadingScreenMessageAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = LoadingScreenMessage.prefix

#     list_display = ('key' ,'english_message', 'spanish_message',)

#     ordering = ('key',)

#     def english_message(self, obj):
#         return obj.message.english
#     english_message.short_description = "EN"

#     def spanish_message(self, obj):
#         return obj.message.spanish
#     spanish_message.short_description = "ES"

class POIForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = POI
        fields = '__all__'

# @admin.register(POI, site=custom_admin_site)
# class POIAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = POI.prefix

#     ordering = ('key',)

#     form = POIForm

#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

#     fieldsets = (
#         ("General", {
#             "fields": ("identifier", "key", "name", "icon_path", "show_at_start", "show_notification", "trigger_conditions"),
#         }),
#         ("Min Bounds", {
#             "fields": ("min_bounds_x", "min_bounds_y"),
#             "description": "Vector2"
#         }),
#         ("Max Bounds", {
#             "fields": (("max_bounds_x", "max_bounds_y")),
#             "description": "Vector2"
#         }),
#     )

# @admin.register(ProjectileType, site=custom_admin_site)
# class ProjectileTypeAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = ProjectileType.prefix
#     list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
#     ordering = ('key',)
        
#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

class ProjectileForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Projectile
        fields = '__all__'

# @admin.register(Projectile, site=custom_admin_site)
# class ProjectileAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = Projectile.prefix
#     list_display = ('identifier', 'key')

#     ordering = ('key',)

#     form = ProjectileForm

class AbilityTreeForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = AbilityTree
        fields = '__all__'

# @admin.register(AbilityTree, site=custom_admin_site)
# class AbilityTreeAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = AbilityTree.prefix
#     list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

#     ordering = ('key',)

#     form = AbilityTreeForm

#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

# @admin.register(AbilityType, site=custom_admin_site)
# class AbilityTypeAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = AbilityType.prefix
#     list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
#     ordering = ('key',)
        
#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

class AbilityForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Ability
        fields = '__all__'

# @admin.register(Ability, site=custom_admin_site)
# class AbilityAdmin(BaseModelAdmin, AutoKeyMixin):
#     key_prefix = Ability.prefix
#     list_display = ('identifier', 'key', 'ability_tree_name', 'english_name', 'spanish_name',)

#     ordering = ('key',)

#     form = AbilityForm

#     def ability_tree_name(self, obj):
#         return obj.ability_tree.identifier
#     ability_tree_name.short_description = "Ability Tree Name"

#     def english_name(self, obj):
#         return obj.name.english
#     english_name.short_description = "EN"

#     def spanish_name(self, obj):
#         return obj.name.spanish
#     spanish_name.short_description = "ES"

class ConditionForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Condition
        fields = '__all__'

@admin.register(Condition, site=custom_admin_site)
class ConditionAdmin(BaseModelAdmin, AutoKeyMixin):
    #TODO: limpiar campos y comentarios sobrantes
    list_display = ('identifier', 'key', 'use_identifier')
    search_fields = ('identifier', 'key')
    ordering = ('key',)

    form = ConditionForm

class BasicDialogueInlineForm(BaseItemInlineForm):
    class Meta:
        model = Basic
        fields = '__all__'

class BasicDialogueInline(admin.StackedInline):
    model = Basic
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = BasicDialogueInlineForm

class QuestPromptDialogueInlineForm(BaseItemInlineForm):
    class Meta:
        model = QuestPrompt
        fields = '__all__'

class QuestPromptDialogueInline(admin.StackedInline):
    model = QuestPrompt
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = QuestPromptDialogueInlineForm

class QuestEndDialogueInlineForm(BaseItemInlineForm):
    class Meta:
        model = QuestEnd
        fields = '__all__'

class QuestEndDialogueInline(admin.StackedInline):
    model = QuestEnd
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    form = QuestEndDialogueInlineForm

class RequiredItemsDialogueInline(admin.TabularInline):
    model = DialogItemsRequired
    extra = 0

class RemoveItemsDialogueInline(admin.TabularInline):
    model = DialogItemsToRemove
    extra = 0

class GiveItemsDialogueInline(admin.TabularInline):
    model = DialogItemsToGive
    extra = 0
    
class DialogueForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Dialogue
        fields = '__all__'

@admin.register(Dialogue, site=custom_admin_site)
class DialogueAdmin(BaseModelAdmin):
    key_prefix = Dialogue.prefix
    list_display = ('identifier', 'key', 'type',)
    list_filter = ("type",)
    search_fields = ('identifier', 'key')
    ordering = ('key',)

    inlines = [
        BasicDialogueInline, 
        QuestPromptDialogueInline, 
        QuestEndDialogueInline, 
        RequiredItemsDialogueInline,
        RemoveItemsDialogueInline,
        GiveItemsDialogueInline,
    ]

    form = DialogueForm

    class Media:
        js = (
            'admin/js/dialogue_auto_key.js',
            'admin/js/dialogue_type_toggle.js',
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # si ya existe, es edición
            return ['type']
        return []

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

class DialogueSingleItemForm(BaseModelForm):
    key_prefix = DialogueSingleItem.prefix

    class Meta:
        model = DialogueSingleItem
        fields = '__all__'
        widgets = {
            'identifier': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
            'key': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
        }  

class DialogueSequenceItemForm(BaseModelForm):
    key_prefix = DialogueSequenceItem.prefix

    class Meta:
        model = DialogueSequenceItem
        fields = '__all__'

class DialogueSingleItemInline(admin.TabularInline):
    model = DialogueSingleItem
    form = DialogueSingleItemForm
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class DialogueSequenceItemInline(admin.TabularInline):
    model = DialogueSequenceItem
    form = DialogueSequenceItemForm
    extra = 1

    class Media:
        js = (
            'admin/js/get_sanitized_key.js', 
            'admin/js/dialogue_item_auto_key_inline.js', 
            'admin/js/tabularinline_items_index_autoincrement.js',
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class DialogueSequenceForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = DialogueSequence
        fields = '__all__'
        widgets = {
            'identifier': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
            'key': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
        } 

@admin.register(DialogueSequence, site=custom_admin_site)
class DialogueSequenceAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = DialogueSequence.prefix
    list_display = ('identifier', 'key',)
    search_fields = ('identifier', 'key',)

    ordering = ('key',)
    inlines = [DialogueSequenceItemInline]
    form = DialogueSequenceForm

@admin.register(DialogueSingleItem, site=custom_admin_site)
class DialogueSingleItemAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = DialogueSingleItem.prefix
    list_display = ('identifier', 'key', 'speaker', 'single_item_text_en', 'single_item_text_es')
    search_fields = ('identifier', 'key')

    ordering = ('key',)

    form = DialogueSingleItemForm

    def single_item_text_en(self,obj):
        return obj.text.english
    single_item_text_en.short_description = "text (EN)"

    def single_item_text_es(self,obj):
        return obj.text.spanish
    single_item_text_es.short_description = "text (ES)"

@admin.register(DialogueSequenceItem, site=custom_admin_site)
class DialogueSequenceItemAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = DialogueSequenceItem.prefix
    list_display = ('identifier', 'key', 'speaker', 'english_text', 'spanish_text',)
    search_fields = ('identifier', 'key')

    ordering = ('key',)

    form = DialogueSequenceItemForm

    def english_text(self, obj):
        return obj.text.english
    english_text.short_description = "EN"

    def spanish_text(self, obj):
        return obj.text.spanish
    spanish_text.short_description = "ES"

class DiaryEntryForm(BaseModelForm):
    key_prefix = DiaryEntry.prefix

    class Meta(BaseModelForm.Meta):
        model = DiaryEntry
        fields = '__all__'

@admin.register(DiaryEntry, site=custom_admin_site)
class DiaryEntryAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = DiaryEntry.prefix
    list_display = ('identifier', 'key','english_title', 'spanish_title', 'english_text', 'spanish_text',)
    
    ordering = ('key',)

    form = DiaryEntryForm

    def english_title(self, obj):
        return obj.title.english
    english_title.short_description = "Title (EN)"

    def spanish_title(self, obj):
        return obj.title.spanish
    spanish_title.short_description = "Title (ES)"

    def english_text(self, obj):
        return obj.text.english
    english_text.short_description = "Text (EN)"

    def spanish_text(self, obj):
        return obj.text.spanish
    spanish_text.short_description = "Text (ES)"

class DiaryPageForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = DiaryPage
        fields = '__all__'

class DiaryEntryInline(admin.TabularInline):
    model = DiaryEntry
    form = DiaryEntryForm
    extra = 1

    class Media:
        js = (
            'admin/js/get_sanitized_key.js',
            'admin/js/diary_entry_auto_key_inline.js',
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DiaryPage, site=custom_admin_site)
class DiaryPageAdmin(BaseModelAdmin, AutoKeyMixin):
    key_prefix = DiaryPage.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    inlines = [DiaryEntryInline]

    ordering = ('key',)

    form = DiaryPageForm

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

class WeaponAttackSequenceForm(BaseItemInlineForm):
    class Meta(BaseModelForm.Meta):
        model = WeaponAttackSequence
        fields = '__all__'

class WeaponAttackSequenceInline(admin.TabularInline):
    model = WeaponAttackSequence
    form = WeaponAttackSequenceForm
    extra = 1

    class Media:
        js = (
            'admin/js/get_sanitized_key.js', 
            'admin/js/tabularinline_weapon_attack_sequence_index_autoincrement.js',
        )

# Agregar para ver si los items y los subtipos se están creando bien.
@admin.register(Weapon, site=custom_admin_site)
class WeaponAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'key', 'sequence')
    inlines = [WeaponAttackSequenceInline,]

    def has_add_permission(self, request):
        return False
    
    def identifier(self, obj):
        return obj.item.identifier
    identifier.short_description = "Identifier"

    def key(self, obj):
        return obj.item.key
    key.short_description = "Key"

    def sequence(self, obj):
        sequences = obj.weaponattacksequence_set.all().order_by("index")
        return " | ".join(
            [f"{seq.attack_sequence.identifier}" for seq in sequences]
        )

# @admin.register(Consumable, site=custom_admin_site)
# class ConsumablenAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False

# @admin.register(Equipment, site=custom_admin_site)
# class EquipmentAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False

# @admin.register(QuestItem, site=custom_admin_site)
# class QuestItemAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False

# @admin.register(ItemAttributes, site=custom_admin_site)
# class ItemAttributesAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False

# @admin.register(QuestEnd, site=custom_admin_site)
# class QuestEndAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False

#TODO: Arbol de dependencias para las conditions
# Es decir
# Listar todas las conditions triggereadas por todos los elementos
# y para cada condition trigereada quien la escucha