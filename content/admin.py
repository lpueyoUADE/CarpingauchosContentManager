from django import forms
from django.contrib import admin, messages
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, OneToOneField, ForeignKey, CASCADE
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

        print(data)

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

custom_admin_site = CustomAdminSite(name='custom_admin')

def _add_localization_field_filter(key_prefix, db_field, kwargs):
    """
    Filtro para los campos de Tipo Localization.
    Solo muestra los locs. del mismo prefijo que el modelo a cargar.
    """
    if db_field.related_model == Localization:
        # Filtramos por key que contenga cierto texto
        kwargs["queryset"] = Localization.objects.filter(Q(key__icontains=key_prefix) & Q(key__icontains=db_field.name)).order_by('key')

class BaseModelAdmin(admin.ModelAdmin):
    key_prefix = ''

    class Media:
        js = ('admin/js/auto_key.js', 'admin/js/auto_localizations.js', 'admin/js/file_grid.js')

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
                widget=PrefabGridWidget()
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

@admin.register(Localization, site=custom_admin_site)
class LocalizationAdmin(BaseModelAdmin):
    key_prefix = Localization.prefix

    list_display = ('key', 'model_name', 'english', 'spanish')
    ordering = ('key',)

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
        js = ('admin/js/auto_key_inline.js', 'admin/js/tabularinline_questobjectives_index_autoincrement.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(QuestObjective, site=custom_admin_site)
class QuestObjectiveAdmin(BaseModelAdmin):
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
class NPCAdmin(BaseModelAdmin):
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
class QuestAdmin(BaseModelAdmin):
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
                widget=PrefabGridWidget()
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
        model = Weapon
        fields = '__all__'

class QuestItemInlineForm(BaseItemInlineForm):
    class Meta:
        model = QuestItem
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

class ItemForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Item
        fields = ('identifier', 'key', 'rarity', 'type', 'name', 'description', 'value', 'icon_path')

@admin.register(WeaponType, site=custom_admin_site)
class WeaponTypeAdmin(BaseModelAdmin):
    key_prefix = WeaponType.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)
        
    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

@admin.register(DamageType, site=custom_admin_site)
class DamageTypeAdmin(BaseModelAdmin):
    key_prefix = DamageType.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)
   
    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

@admin.register(EquipmentType, site=custom_admin_site)
class EquipmentTypeAdmin(BaseModelAdmin):
    key_prefix = EquipmentType.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)
        
    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

class AttackSequenceForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = AttackSequence
        fields = '__all__'

@admin.register(AttackSequence, site=custom_admin_site)
class AttackSequenceAdmin(BaseModelAdmin):
    key_prefix = AttackSequence.prefix

    form = AttackSequenceForm

@admin.register(Item, site=custom_admin_site)
class ItemAdmin(BaseModelAdmin):
    key_prefix = Item.prefix
    list_display = ('identifier', 'key', 'type', 'rarity_name', 'english_name', 'spanish_name',)
    ordering = ('key', 'type')

    inlines = [
        WeaponInline, EquipmentInline, ConsumableInline, QuestItemInline
    ]

    form = ItemForm

    class Media:
        js = ('admin/js/item_auto_key.js', 'admin/js/item_type_toggle.js')

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

class RarityForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Rarity
        fields = '__all__'
        widgets = {
            'color_start': forms.TextInput(attrs={'type': 'color'}),
            'color_end': forms.TextInput(attrs={'type': 'color'}),
        }

@admin.register(Rarity, site=custom_admin_site)
class RarityAdmin(BaseModelAdmin):
    key_prefix = Rarity.prefix
    list_display = ('key', 'gradient_color_start', 'gradient_color_end', 'rarity_name','english_name', 'spanish_name',)

    ordering = ('key',)

    form = RarityForm

    def has_add_permission(self, request, obj=None):
        enabled_views = (
            'index',
            'content_rarity_changelist',
            'content_rarity_add',
            'content_rarity_change'
        )
        return request.resolver_match and request.resolver_match.url_name in enabled_views
    
    def has_delete_permission(self, request, obj=None):
        enabled_views = (
            'index',
            'content_rarity_changelist',
            'content_rarity_add',
            'content_rarity_change'
        )
        return request.resolver_match and request.resolver_match.url_name in enabled_views
    
    def has_change_permission(self, request, obj=None):
        enabled_views = (
            'index',
            'content_rarity_changelist',
            'content_rarity_add',
            'content_rarity_change'
        )
        return request.resolver_match and request.resolver_match.url_name in enabled_views
    

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"
  
    def gradient_color_start(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            obj.color_start,
            obj.color_start
        )
    
    gradient_color_start.short_description = "Color Start"
    
    def gradient_color_end(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            obj.color_end,
            obj.color_end 
        )
    
    gradient_color_end.short_description = "Color End"

    def rarity_name(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            obj.color_start,
            obj.name.english 
        )

    rarity_name.short_description = "Name"
    rarity_name.admin_order_field = 'name'


@admin.register(LoadingScreenMessage, site=custom_admin_site)
class LoadingScreenMessageAdmin(BaseModelAdmin):
    key_prefix = LoadingScreenMessage.prefix

    list_display = ('key' ,'english_message', 'spanish_message',)

    ordering = ('key',)

    def english_message(self, obj):
        return obj.message.english
    english_message.short_description = "EN"

    def spanish_message(self, obj):
        return obj.message.spanish
    spanish_message.short_description = "ES"

class POIForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = POI
        fields = '__all__'

@admin.register(POI, site=custom_admin_site)
class POIAdmin(BaseModelAdmin):
    key_prefix = POI.prefix

    ordering = ('key',)

    form = POIForm

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

    fieldsets = (
        ("General", {
            "fields": ("identifier", "key", "name", "icon_path", "show_at_start", "show_notification", "trigger_conditions"),
        }),
        ("Min Bounds", {
            "fields": ("min_bounds_x", "min_bounds_y"),
            "description": "Vector2"
        }),
        ("Max Bounds", {
            "fields": (("max_bounds_x", "max_bounds_y")),
            "description": "Vector2"
        }),
    )

@admin.register(ProjectileType, site=custom_admin_site)
class ProjectileTypeAdmin(BaseModelAdmin):
    key_prefix = ProjectileType.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)
        
    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

class ProjectileForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Projectile
        fields = '__all__'

@admin.register(Projectile, site=custom_admin_site)
class ProjectileAdmin(BaseModelAdmin):
    key_prefix = Projectile.prefix
    list_display = ('identifier', 'key')

    ordering = ('key',)

    form = ProjectileForm

class AbilityTreeForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = AbilityTree
        fields = '__all__'

@admin.register(AbilityTree, site=custom_admin_site)
class AbilityTreeAdmin(BaseModelAdmin):
    key_prefix = AbilityTree.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    ordering = ('key',)

    form = AbilityTreeForm

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

@admin.register(AbilityType, site=custom_admin_site)
class AbilityTypeAdmin(BaseModelAdmin):
    key_prefix = AbilityType.prefix
    list_display = ('identifier', 'key', 'english_name', 'spanish_name',)
    ordering = ('key',)
        
    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

class AbilityForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Ability
        fields = '__all__'

@admin.register(Ability, site=custom_admin_site)
class AbilityAdmin(BaseModelAdmin):
    key_prefix = Ability.prefix
    list_display = ('identifier', 'key', 'ability_tree_name', 'english_name', 'spanish_name',)

    ordering = ('key',)

    form = AbilityForm

    def ability_tree_name(self, obj):
        return obj.ability_tree.identifier
    ability_tree_name.short_description = "Ability Tree Name"

    def english_name(self, obj):
        return obj.name.english
    english_name.short_description = "EN"

    def spanish_name(self, obj):
        return obj.name.spanish
    spanish_name.short_description = "ES"

class ConditionForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = Condition
        fields = '__all__'

@admin.register(Condition, site=custom_admin_site)
class ConditionAdmin(BaseModelAdmin):
    #TODO: limpiar campos y comentarios sobrantes
    # list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    ordering = ('key',)

    form = ConditionForm

    # def english_name(self, obj):
    #     return obj.name.english
    # english_name.short_description = "EN"

    # def spanish_name(self, obj):
    #     return obj.name.spanish
    # spanish_name.short_description = "ES"

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
        js = ('admin/js/dialogue_item_auto_key_inline.js', 'admin/js/tabularinline_items_index_autoincrement.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class DialogueSequenceForm(BaseModelForm):
    class Meta(BaseModelForm.Meta):
        model = DialogueSequence
        fields = '__all__'

@admin.register(DialogueSequence, site=custom_admin_site)
class DialogueSequenceAdmin(BaseModelAdmin):
    key_prefix = DialogueSequence.prefix
    # list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    ordering = ('key',)
    inlines = [DialogueSequenceItemInline]
    form = DialogueSequenceForm

@admin.register(DialogueSingleItem, site=custom_admin_site)
class DialogueSingleItemAdmin(BaseModelAdmin):
    key_prefix = DialogueSingleItem.prefix
    # list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    ordering = ('key',)

    form = DialogueSingleItemForm

    # class Media:
    #     js = (
    #         'admin/js/auto_localizations.js',
    #     )

    # def english_name(self, obj):
    #     return obj.name.english
    # english_name.short_description = "EN"

    # def spanish_name(self, obj):
    #     return obj.name.spanish
    # spanish_name.short_description = "ES"

@admin.register(DialogueSequenceItem, site=custom_admin_site)
class DialogueSequenceItemAdmin(BaseModelAdmin):
    key_prefix = DialogueSequenceItem.prefix
    # list_display = ('identifier', 'key', 'english_name', 'spanish_name',)

    ordering = ('key',)

    form = DialogueSequenceItemForm

    # def english_name(self, obj):
    #     return obj.name.english
    # english_name.short_description = "EN"

    # def spanish_name(self, obj):
    #     return obj.name.spanish
    # spanish_name.short_description = "ES"

class DiaryEntryForm(BaseModelForm):
    key_prefix = DiaryEntry.prefix

    class Meta(BaseModelForm.Meta):
        model = DiaryEntry
        fields = '__all__'

@admin.register(DiaryEntry, site=custom_admin_site)
class DiaryEntryAdmin(BaseModelAdmin):
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
        js = ('admin/js/diary_entry_auto_key_inline.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Verificamos si el campo apunta a Localization
        _add_localization_field_filter(self.model.prefix, db_field, kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DiaryPage, site=custom_admin_site)
class DiaryPageAdmin(BaseModelAdmin):
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

# Agregar para ver si los items y los subtipos se están creando bien.
# @admin.register(Weapon, site=custom_admin_site)
# class WeaponAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False

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

#TODO: Arbol de dependencias para las conditions
# Es decir
# Listar todas las conditions triggereadas por todos los elementos
# y para cada condition trigereada quien la escucha