from django import forms
from django.contrib import admin, messages
from django.db.models import OneToOneField, ForeignKey, CASCADE
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect, HttpResponse
from django.core.serializers import serialize
from django.conf import settings
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
    )

from io import StringIO
import json
import os
from datetime import datetime


class CustomAdminSite(admin.AdminSite):
    site_header = "Carpingauchos Content Manager"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("export-localization/", self.admin_view(self.export_localization), name="export-localization"),
            path("download-localization/", self.admin_view(self.download_localization), name="download-localization"),
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
    
    def download_localization(self, request):
        buffer = StringIO()

        # Serializamos múltiples modelos y los agregamos al buffer como una lista JSON
        data = {
            'Rarity': Rarity.to_dict(),
            'WeaponType': WeaponType.to_dict(),
            'EquipmentType': EquipmentType.to_dict(),
            'Localization': Localization.to_dict(),
            'Item': {
                'Weapon': Item.to_dict(Weapon),
                'Equipment': Item.to_dict(Equipment),
                'Consumable': Item.to_dict(Consumable),
                'Quest': Item.to_dict(QuestItem),
            },
            'Quest': Quest.to_dict(),
            'QuestObjective': QuestObjective.to_dict(),
        }

        # Convertimos a JSON final
        json.dump(data, buffer, indent=4, ensure_ascii=False)

        today = datetime.now().strftime("%d-%m-%Y")
        filename = f"full_export_{today}.json"

        response = HttpResponse(buffer.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, "Exportación completa generada y descargada.")
        return response

        
custom_admin_site = CustomAdminSite(name='custom_admin')


class BaseModelAdmin(admin.ModelAdmin):
    key_prefix = ''

    class Media:
        js = ('admin/js/auto_key.js', 'admin/js/auto_localizations.js')

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
    
class BaseModelForm(forms.ModelForm):
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

    class Meta:
        model = Localization
        fields = '__all__'
        readonly_fields = ('identifier',)

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

    list_display = ('key', 'english', 'spanish')
    ordering = ('key',)

    form = LocalizationForm

    def has_add_permission(self, request):
        can_add_localizations = (
            'content_item_add',
            'content_quest_add',
            'content_rarity_add',
            'content_localization_add',
            'content_equipmenttype_add',
            'content_damagetype_add',
            'content_weapontype_add',
            'content_npc_add',
            'content_npc_change',
        )
        return request.resolver_match and request.resolver_match.url_name in can_add_localizations
    
class QuestObjectiveForm(BaseModelForm):
    key_prefix = QuestObjective.prefix

    class Meta:
        model = QuestObjective
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['key'].widget.attrs['readonly'] = True
        self.fields['identifier'].widget.attrs['data-key-prefix'] = self.key_prefix

class QuestObjectiveInline(admin.TabularInline):
    model = QuestObjective
    form = QuestObjectiveForm

    extra = 1  # cuántos formularios vacíos mostrar para crear nuevos objetivos

    class Media:
        js = ('admin/js/auto_key_inline.js',)

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
    class Meta:
        model = Quest
        fields = '__all__'
        widgets = {
            'money_reward': forms.NumberInput(attrs={'min': 0}),
            'ability_points_reward': forms.NumberInput(attrs={'min': 0}),
        }

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
    def has_changed(self):
        """ Should returns True if data differs from initial. 
        By always returning true even unchanged inlines will get validated and saved."""
        return True

class ConsumableInlineForm(BaseItemInlineForm):
    class Meta:
        model = Consumable
        fields = '__all__'
        widgets = {
            'cooldown': forms.NumberInput(attrs={'min': 0}),
            'effect_Duration': forms.NumberInput(attrs={'min': 0}),
            'physical_Resistance_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'magical_resistance_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'heal_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'mana_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'stamina_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_stamina_regen_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'nerf_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'nerf_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'extra_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'extra_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'give_flat_health': forms.NumberInput(attrs={'min': 0}),
            'give_flat_mana': forms.NumberInput(attrs={'min': 0}),
            'give_flat_stamina': forms.NumberInput(attrs={'min': 0}),
        }

class WeaponInlineForm(BaseItemInlineForm):
    class Meta:
        model = Weapon
        fields = '__all__'
        widgets = {
            'poise_break_force': forms.NumberInput(attrs={'min': 0}),
            'flat_physical_damage': forms.NumberInput(attrs={'min': 0}),
            'flat_magical_damage': forms.NumberInput(attrs={'min': 0}),
            'physical_resistance_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'magical_resistance_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_health_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_mana_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_stamina_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_stamina_regen_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'nerf_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'nerf_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'extra_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'extra_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'attack_stamina_cost': forms.NumberInput(attrs={'min': 0}),
        }
class EquipmentInlineForm(BaseItemInlineForm):
    class Meta:
        model = Weapon
        fields = '__all__'
        widgets = {
            'flat_physical_damage': forms.NumberInput(attrs={'min': 0}),
            'flat_magical_damage': forms.NumberInput(attrs={'min': 0}),
            'physical_resistance_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'magical_resistance_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_health_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_mana_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_stamina_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'buff_stamina_regen_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'nerf_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'nerf_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'extra_physical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'extra_magical_damage_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'stamina_cost': forms.NumberInput(attrs={'min': 0}),
        }

class QuestItemInlineForm(BaseItemInlineForm):
    class Meta:
        model = QuestItem
        fields = '__all__'

class ConsumableInline(admin.StackedInline):
    model = Consumable
    extra = 1
    min_num = 0
    max_num = 1
    can_delete = False

    form = ConsumableInlineForm

class WeaponInline(admin.StackedInline):
    model = Weapon
    extra = 1
    min_num = 0
    max_num = 1
    can_delete = False

    form = WeaponInlineForm

class EquipmentInline(admin.StackedInline):
    model = Equipment
    extra = 1
    min_num = 0
    max_num = 1
    can_delete = False

    form = EquipmentInlineForm

class QuestItemInline(admin.StackedInline):
    model = QuestItem
    extra = 1
    min_num = 0
    max_num = 1
    can_delete = False

    form = QuestItemInlineForm

class ItemForm(BaseModelForm):
    class Meta:
        model = Item
        fields = ('identifier', 'key', 'rarity', 'type', 'name', 'description', 'value', 'icon_path')
        widgets = {
            **BaseModelForm.Meta.widgets,
            'value': forms.NumberInput(attrs={'min': 0}),
        }

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
                obj.rarity.color,
                obj.rarity.name.english 
            )
    rarity_name.short_description = "Rarity"
    rarity_name.admin_order_field = 'rarity'

class RarityForm(BaseModelForm):
    class Meta:
        model = Rarity
        fields = '__all__'
        widgets = {
            **BaseModelForm.Meta.widgets,
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

@admin.register(Rarity, site=custom_admin_site)
class RarityAdmin(BaseModelAdmin):
    key_prefix = Rarity.prefix
    list_display = ('key', 'color', 'rarity_name','english_name', 'spanish_name',)

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
  
    def rarity_name(self, obj):
        return format_html(
                '<span style="color: {};">{}</span>',
                obj.color,
                obj.name.english 
            )
    rarity_name.short_description = "Name"
    rarity_name.admin_order_field = 'name'

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
