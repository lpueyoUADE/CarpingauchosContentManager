from django.db import models
from django.db.models import OneToOneField
from django.forms.models import model_to_dict
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import slugify

class LocalizedField(models.OneToOneField):
    """
    ModelField para campos localizados.
    """
    def __init__(self, *args, **kwargs):
        """
        Se define como un oneToOne común pero se omite el modelo de referencia ya que se asume
        Localization.
        """

        # Help text por defecto.
        kwargs.setdefault("help_text", "Texto Localizado.")

        # To Localization.
        kwargs.setdefault("to", Localization)
        super().__init__(*args, **kwargs)

def _get_related_one_to_one(instance, related_name):        
        related_object = getattr(instance, related_name)
        result = related_object.to_dict_item()
        return result

def _get_related_objects(instance, related_name, *select_related_fields, sort_lambda_key=None, reversed=False):
    related_objects = getattr(instance, related_name)

    result = [related_instance.to_dict_item() for related_instance in related_objects.select_related(*select_related_fields)]

    if sort_lambda_key:
        result.sort(key=lambda item: item[sort_lambda_key], reverse=reversed)

    return result

class BaseModel(models.Model):
    prefix = ''

    identifier =  models.CharField(max_length=150, null=False, blank=False, help_text="Texto identificador del recurso.")
    key = models.SlugField(max_length=150, unique=True, null=False, blank=False, help_text="Texto autogenerado.")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.key = slugify(self.key)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.key
    
    @classmethod
    def _get_localization_fields_to_delete(cls, model):
        return [
            f for f in model._meta.get_fields()
            if isinstance(f, OneToOneField) and f.related_model == Localization
        ]    

    @classmethod
    def _on_post_delete(cls, instance, **kwargs):
        """
        Busca dentro del modelo las referencias a Localization
        que van a ser borradas y ejecuta el delete los objetos.

        No hace falta buscar las foreign keys hacia el propio objeto
        porque esas se borran por defecto con el delete CASCADE.
        """

        for field in cls._get_localization_fields_to_delete(cls):
            related_obj = getattr(instance, field.name)
            if related_obj:
                related_obj.delete()

    @classmethod
    def to_dict(cls, fields_to_remove=None, fields_to_localize=None, extra_process=None, **filters):
        result = []

        if isinstance(fields_to_localize, list):
            fields_to_localize_names = [f.field.name for f in fields_to_localize]

        else:
            fields_to_localize_names = []
    
        if isinstance(fields_to_remove, list):
            fields_to_remove_names = [f.field.name for f in fields_to_remove]
        
        else:
            fields_to_remove_names = []
    
        elements = cls.objects.select_related(*fields_to_localize_names).filter(**filters)

        for element in elements:
            data = model_to_dict(element)

            # En Unity no usamos ids sino las keys de los items.
            data.pop('id')

            for field_remove in fields_to_remove_names:
                data.pop(field_remove)

            for field_name in fields_to_localize_names:
                data.pop(field_name)
                data[field_name + "_localization_key"] = getattr(element, field_name).key

            if extra_process:
                extra_process(element, data)

            result.append(data)

        return result

    #TODO: Remover los to_dict originales porque ya no se van a usar incluso algunos modelos cambiaron.
    @classmethod
    def to_dict2(cls, json_field_name, *fields_to_select_related, **filters):
        """
        Devuelve un diccionario con todas las instancias de un modelo convertidas a diccionario.
        """
        return {
            json_field_name: cls.get_objects(*fields_to_select_related, **filters)
        }

    @classmethod
    def get_objects(cls, *fields_to_localize, **filters):
        """
        Devuelve todas las instancias del modelo convertidos a diccionario.
        """
        fields_to_localize_names = [f.field.name for f in fields_to_localize]
        objects = cls.objects.select_related(*fields_to_localize_names).filter(**filters)
    
        return [obj.to_dict_item() for obj in objects]

    def get_related_one_to_one(self, related_name):
        """
        Devuelve la instancia de un modelo relacionado por related_name en un 1 to 1.
        """
        return _get_related_one_to_one(self, related_name)

    def get_related_objects(self, related_name, *select_related_fields, sort_lambda_key=None, reversed=False):
        """
        Devuelve todas las intancias de un modelo relacionado por related_name en M2M o FK.
        """
        return _get_related_objects(self, related_name, *select_related_fields, sort_lambda_key=sort_lambda_key, reversed=reversed)
        
    
class Localization(BaseModel):
    prefix = 'loc_'

    """
    Localization entries are not intended to be set directly through this model. Related models
    like Quests or Items should create a new entry when creating a new Item or Quest.
    """
    english = models.TextField(null=True, blank=True, default="")
    spanish = models.TextField(null=True, blank=True, default="")

class NPC(BaseModel):
    prefix = 'npc_'
    name = LocalizedField(related_name='npc_name', on_delete=models.CASCADE)
    
    @classmethod
    def extra_process(cls, npc_element, data):
        first_talk_dialogues = []
        dialogues = []

        for dialogue in npc_element.dialogues.all():
            if dialogue.type == DialogueTypes.BASIC and dialogue.basic_dialogue.is_first_talk:
                first_talk_dialogues.append(dialogue.key)

            else:
                dialogues.append(dialogue.key)

        data['first_talk_dialogue_keys'] = first_talk_dialogues
        data['dialogue_keys'] = dialogues
        
    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [NPC.name], cls.extra_process)

class Quest(BaseModel):
    prefix = 'quest_'
    title = LocalizedField(related_name='quest_title', on_delete=models.CASCADE)
    brief = LocalizedField(related_name='quest_brief', on_delete=models.CASCADE)

    money_reward = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])
    ability_points_reward = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])
    
    items_reward = models.ManyToManyField('Item', related_name='quests_rewarded', through='ItemReward', blank=True)

    npc_giver = models.ForeignKey(NPC, related_name='quests', on_delete=models.CASCADE, default=None)

    @classmethod
    def extra_process(cls, quest_element, data):
        data['npc_giver'] = quest_element.npc_giver.key

        item_rewards_list = []

        item_rewards = quest_element.itemreward_set.select_related('item')

        for item_reward in item_rewards:
            item_rewards_list.append({
                'item_key': item_reward.item.key,
                'amount': item_reward.amount
            })

        data['items_reward'] = item_rewards_list

        objectives = []
        for objective in quest_element.objectives.all():
            objectives.append(objective.key)

        data['objectives'] = objectives
        
    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [Quest.title, Quest.brief], cls.extra_process)

    @classmethod
    def to_dict2(cls):
        return super().to_dict2("Quests", Quest.title, Quest.brief)

    def to_dict_item(self):
        return {
            "ID": self.key,
            "TitleKey": self.title.key,
            "BriefKey": self.brief.key,
            "Objectives": self.get_related_objects(related_name="objectives", sort_lambda_key="index"),
            "RewardMoney": self.money_reward,
            "RewardAbilityPoints": self.ability_points_reward,
            "RewardsItems": self.get_related_objects("itemreward_set", "item"),
        }

class QuestObjective(BaseModel):
    prefix = 'questobjective_'

    index = models.PositiveIntegerField(default=1, help_text='Orden del objetivo', validators=[MinValueValidator(1), MaxValueValidator(1000)])

    brief = LocalizedField(related_name='quest_objective_brief', on_delete=models.CASCADE)
    is_trackeable = models.BooleanField(default=True)
    
    quest = models.ForeignKey(Quest, related_name='objectives', on_delete=models.CASCADE)

    @classmethod
    def extra_process(cls, element, data):
        data['quest'] = element.quest.key

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [QuestObjective.brief], cls.extra_process)

    def to_dict_item(self):
        return {
            "index": self.index,
            "ID": self.key,
            "TextLocalizedKey": self.brief.key,
            "IsAddedToCompletitions": self.is_trackeable,
        }


class Rarity(BaseModel):
    prefix = 'rarity_'
    name = LocalizedField(related_name='rarity_name', on_delete=models.CASCADE)
    rarity_json_id = models.IntegerField(default=0, validators=[MinValueValidator(0)], unique=True)
    color_start = models.CharField(
        max_length=7,
        default="#FFFFFF",
        help_text="Color incial de gradiente."
    )

    color_end = models.CharField(
        max_length=7,
        default="#FFFFFF",
        help_text="Color final de gradiente."
    )

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [Rarity.name])

class ItemAttributes(models.Model):
    item = models.OneToOneField("Item", on_delete=models.CASCADE, related_name="itemattributes_item")

    def __str__(self):
        return self.item.key

    # Items
    flat_physical_damage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    flat_magical_damage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    armor_physical_resistance = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    armor_magical_resistance = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Timing
    cooldown = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    duration = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    # Costs
    cost_health = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    cost_mana = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    cost_stamina = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    # Gives
    give_health = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    give_mana = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    give_stamina = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    # Buffs
    buff_health_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_mana_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_stamina_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_physical_damage_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_magical_damage_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_stamina_regeneration_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Nerfs
    nerf_physical_damage_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    nerf_magical_damage_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    nerf_extra_physical_damage_received_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    nerf_extra_magical_damage_received_percent = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def to_dict_item(self):
        return {
            "Cooldown": {
                "AttType": 1,
                "Value": self.cooldown
            },
            "Duration": {
                "AttType": 2,
                "Value": self.duration
            },
            "Flat_PhysicalDamage": {
                "AttType": 3,
                "Value": self.flat_physical_damage
            },
            "Flat_MagicalDamage": {
                "AttType": 4,
                "Value": self.flat_magical_damage
            },
            "Armor_PhysicalResistance": {
                "AttType": 5,
                "Value": self.armor_physical_resistance / 100
            },
            "Armor_MagicalResistance": {
                "AttType": 6,
                "Value": self.armor_magical_resistance / 100
            },
            "Cost_Health": {
                "AttType": 7,
                "Value": self.cost_health
            },
            "Cost_Mana": {
                "AttType": 8,
                "Value": self.cost_mana
            },
            "Cost_Stamina": {
                "AttType": 9,
                "Value": self.cost_stamina
            },
            "Give_Health": {
                "AttType": 10,
                "Value": self.give_health
            },
            "Give_Mana": {
                "AttType": 11,
                "Value": self.give_mana
            },
            "Give_Stamina": {
                "AttType": 12,
                "Value": self.give_stamina
            },
            "Buff_HealthPercent": {
                "AttType": 13,
                "Value": self.buff_health_percent / 100
            },
            "Buff_ManaPercent": {
                "AttType": 14,
                "Value": self.buff_mana_percent / 100
            },
            "Buff_StaminaPercent": {
                "AttType": 15,
                "Value": self.buff_stamina_percent / 100
            },
            "Buff_PhysicalDamagePercent": {
                "AttType": 16,
                "Value": self.buff_physical_damage_percent / 100
            },
            "Buff_MagicalDamagePercent": {
                "AttType": 17,
                "Value": self.buff_magical_damage_percent / 100
            },
            "Buff_StaminaRegenerationPercent": {
                "AttType": 18,
                "Value": self.buff_stamina_regeneration_percent / 100
            },
            "Nerf_PhysicalDamagePercent": {
                "AttType": 19,
                "Value": self.nerf_physical_damage_percent / 100
            },
            "Nerf_MagicalDamagePercent": {
                "AttType": 20,
                "Value": self.nerf_magical_damage_percent / 100
            },
            "Nerf_ExtraPhysicalDamageReceivedPercent": {
                "AttType": 21,
                "Value": self.nerf_extra_physical_damage_received_percent / 100
            },
            "Nerf_ExtraMagicalDamageReceivedPercent": {
                "AttType": 22,
                "Value": self.nerf_extra_magical_damage_received_percent / 100
            }
        }

class ItemTypes(models.TextChoices):
    WEAPON = 'weapon', 'Weapon'
    EQUIPMENT = 'equipment', 'Equipment'
    CONSUMABLE = 'consumable', 'Consumable'
    QUEST = 'quest_item', 'Quest Item'

class Item(BaseModel):
    prefix = 'item_'

    name = LocalizedField(related_name='item_name', on_delete=models.CASCADE)
    description = LocalizedField(related_name='item_description', on_delete=models.CASCADE)

    rarity = models.ForeignKey(Rarity, related_name='item_rarity', on_delete=models.PROTECT)
    value =  models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10000000)])

    icon_path = models.TextField(null=True, blank=True, default="")
    mesh_path = models.TextField(null=True, blank=True, default="")

    type = models.CharField(max_length=20, null=False, blank=False, choices=ItemTypes.choices)

    @classmethod
    def process_subtype(cls, subtype, element, data):
        """
            Process a single subtype instance.
        """
        # Obtengo el subtype asociado al item
        reverse_name = subtype.item.field.related_query_name()

        # Convierto el subtype a dict
        element_data = getattr(element, reverse_name).to_dict()

        data.update(element_data)

    @classmethod
    def to_dict(cls, subtype):
        extra_process = lambda element, data : cls.process_subtype(subtype, element, data)

        return super().to_dict([Item.type], [Item.name, Item.description, Item.rarity], extra_process, type=subtype.type)

    @classmethod
    def to_dict2(cls):
        return (
            super().to_dict2("ConsumableItems", Item.name, Item.description, Item.rarity, type=Consumable.type) | 
            super().to_dict2("WeaponItems", Item.name, Item.description, Item.rarity, type=Weapon.type) |
            super().to_dict2("ArmorItems", Item.name, Item.description, Item.rarity, type=Equipment.type) |
            super().to_dict2("KeyItems", Item.name, Item.description, Item.rarity, type=QuestItem.type)
        )
    
    def to_dict_item(self):
        if self.type == ItemTypes.CONSUMABLE:
            item_subtype = self.get_related_one_to_one(related_name="consumable_item")
        
        elif self.type == ItemTypes.WEAPON:
            item_subtype = self.get_related_one_to_one(related_name="weapon_item")

        elif self.type == ItemTypes.EQUIPMENT:
            item_subtype = self.get_related_one_to_one(related_name="equipment_item")

        elif self.type == ItemTypes.QUEST:
            item_subtype = self.get_related_one_to_one(related_name="quest_item")

        return {
            "ItemData": {
                "ID": self.key,
                "NameKey": self.name.key,
                "DescriptionKey": self.description.key,
                "Rarity": self.rarity.rarity_json_id,
                "Value": self.value,
                "Icon": self.icon_path,
                "MeshPath": self.mesh_path,
                "Attributes": self.get_related_one_to_one(related_name="itemattributes_item")
            } 
        } | item_subtype

class ItemSubtype(models.Model):
    type = None
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="subtype_item")

    def __str__(self):
        return self.item.key

    class Meta:
        abstract = True
    
    def to_dict(self, *fields_to_convert):
        fields = {}

        data = model_to_dict(self)

        # En Unity no usamos ids sino las keys de los items.
        data.pop('id')

        # No necesito la referencia al Item.
        data.pop('item')

        for field in fields_to_convert:
            field_name = field.field.name
            data[field_name] = getattr(self, field_name).key

        fields.update(data)

        return fields

class ItemReward(models.Model):
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    def __str__(self):
        return f'Quest: {self.quest.key} - Item: {self.item.key} - Amount: {self.amount}'

    def to_dict_item(self):
        return {
            "ID": self.item.key,
            "Quantity": self.amount
        }

class Consumable(ItemSubtype):
    type = ItemTypes.CONSUMABLE
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="consumable_item")

    is_single_effect = models.BooleanField(default=True)
    
    def to_dict_item(self):
        return {
            "SingleEffect": self.is_single_effect,
        }

class WeaponType(BaseModel):
    prefix = "weapontype_"
    name = LocalizedField(related_name='weapon_type_name', on_delete=models.CASCADE)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [WeaponType.name])

class DamageType(BaseModel):
    prefix = "damagetype_"
    name = LocalizedField(related_name='damage_type_name', on_delete=models.CASCADE)
    damage_type_id = models.IntegerField(default=0, validators=[MinValueValidator(0)], unique=True)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [DamageType.name])

class AttackSequence(BaseModel):
    prefix ="attack_sequence_"

    def to_dict_item(self):
        return self.identifier

class WeaponAttackSequence(models.Model):
    weapon = models.ForeignKey('Weapon', on_delete=models.CASCADE)
    attack_sequence = models.ForeignKey(AttackSequence, on_delete=models.CASCADE)
    index = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    def __str__(self):
        return f'Weapon: {self.weapon} - attack_sequence: {self.attack_sequence.key} - Index: {self.index}'

    def to_dict_item(self):
        return self.attack_sequence.identifier

class Weapon(ItemSubtype):
    type = ItemTypes.WEAPON
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="weapon_item")
    
    weapon_type = models.ForeignKey(WeaponType, related_name='weapon_type', on_delete=models.PROTECT) 
    damage_type = models.ForeignKey(DamageType, related_name='damage_type', on_delete=models.PROTECT)

    attack_sequence = models.ManyToManyField(AttackSequence, related_name='weapons', through=WeaponAttackSequence, blank=True)

    poise_break_force = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    physical_damage_absorption_while_blocking = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    magical_damage_absorption_while_blocking = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    prefab = models.TextField(null=True, blank=True, default="")
    
    def to_dict(self):
        fields = super().to_dict(Weapon.weapon_type, Weapon.damage_type)

        fields['attack_sequence'] = [attack_sequence.key for attack_sequence in fields['attack_sequence']]
        fields['attack_sequence'].sort()

        return fields

    def to_dict_item(self):
        return {
            "AttackSequence": _get_related_objects(self, "weaponattacksequence_set", "attack_sequence"),
            "DamageType": self.damage_type.damage_type_id,
            "PoiseBreakForce": self.poise_break_force,
            "PhysicalDamageAbsorptionWhileBlocking": self.physical_damage_absorption_while_blocking,
            "MagicalDamageAbsorptionWhileBlocking": self.magical_damage_absorption_while_blocking,
            "Prefab": self.prefab
        }

class EquipmentType(BaseModel):
    prefix = "equipmenttype_"
    name = LocalizedField(related_name='equipment_type_name', on_delete=models.CASCADE)
    part_id = models.IntegerField(default=1, validators=[MinValueValidator(1)], unique=True)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [EquipmentType.name])
    
    def to_dict_item(self):
        return {
            "Part": self.part_id,
        }

class Equipment(ItemSubtype):
    type = ItemTypes.EQUIPMENT

    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="equipment_item")
    equipment_type = models.ForeignKey(EquipmentType, related_name='equipment_type', on_delete=models.PROTECT)

    prefab = models.TextField(null=True, blank=True, default="")

    def to_dict(self):
        return super().to_dict(Equipment.equipment_type)

    def to_dict_item(self):
        return {
            "Part": self.equipment_type.part_id,
            "Prefab": self.prefab,
        }

class QuestItem(ItemSubtype):
    type = ItemTypes.QUEST
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="quest_item")

    def to_dict_item(self):
        return {}

class LoadingScreenMessage(BaseModel):
    prefix = 'loading_screen_msg_'

    message = LocalizedField(related_name='loading_screen_message', on_delete=models.CASCADE)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [LoadingScreenMessage.message])

class POI(BaseModel):
    """
    Point of Interest.
    """
    prefix = "poi_"
    
    name = LocalizedField(related_name='poi_name', on_delete=models.CASCADE)

    icon_path = models.TextField(null=True, blank=True, default="")
    
    show_at_start = models.BooleanField(default=False)
    show_notification = models.BooleanField(default=True)

    trigger_conditions = models.ManyToManyField('Condition', related_name='poi_conditions_to_trigger',blank=True)

    min_bounds_x = models.FloatField(null=False, blank=False, default=0.0)
    min_bounds_y = models.FloatField(null=False, blank=False, default=0.0)

    max_bounds_x = models.FloatField(null=False, blank=False, default=0.0)
    max_bounds_y = models.FloatField(null=False, blank=False, default=0.0)

    @classmethod
    def extra_process(cls, poi_element, data):
        data["trigger_conditions"] = [tc.key for tc in poi_element.trigger_conditions.all()]

        data['min_bounds'] = {
            'x': poi_element.min_bounds_x,
            'y': poi_element.min_bounds_y,
        }

        data['max_bounds'] = {
            'x': poi_element.max_bounds_x,
            'y': poi_element.max_bounds_y,
        }

    @classmethod
    def to_dict(cls):
        return super().to_dict([POI.min_bounds_x, POI.min_bounds_y,POI.max_bounds_x,POI.max_bounds_y], [POI.name], cls.extra_process)
  
class ProjectileType(BaseModel):
    prefix = "projectiletype_"

class Projectile(BaseModel):
    prefix = "projectile_"

    prefab = models.TextField(null=True, blank=True, default="")

    type = models.ForeignKey(ProjectileType, related_name='projectile_type', on_delete=models.PROTECT)

    speed = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(50)])
    life_time = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(.1), MaxValueValidator(15)])
    radius = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(.1), MaxValueValidator(5)])

    apply_gravity = models.BooleanField(default=True) 
    
    gravity_scale = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    drag_coefficient = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(.1), MaxValueValidator(1)])
    velocity_decay_factor = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(.1), MaxValueValidator(1)])
    minimum_speed = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(.1), MaxValueValidator(1)])
    rotation_speed = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])

    extra_param_1 = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    extra_param_2 = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    extra_param_3 = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    extra_param_4 = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    extra_param_5 = models.FloatField(null=False, blank=False, default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])

    @classmethod
    def extra_process(cls, projectile_element, data):
        data['type'] = projectile_element.type.key

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, None, cls.extra_process)

class AbilityTree(BaseModel):
    prefix = 'abilitytree_'

    name = LocalizedField(related_name='ability_tree_name', on_delete=models.CASCADE)
    slogan = LocalizedField(related_name='ability_tree_slogan', on_delete=models.CASCADE)
    description = LocalizedField(related_name='ability_tree_description', on_delete=models.CASCADE)

    icon_path = models.TextField(null=True, blank=True, default="")

    @classmethod
    def extra_process(cls, ability_tree_element, data):
        pass

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [AbilityTree.name, AbilityTree.slogan, AbilityTree.description], cls.extra_process)

class AbilityType(BaseModel):
    prefix = "abilitytype_"
    name = LocalizedField(related_name='ability_type_name', on_delete=models.CASCADE)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [AbilityType.name])

class Ability(BaseModel):
    prefix = 'ability_'

    ability_tree = models.ForeignKey(AbilityTree, related_name='abilities', on_delete=models.PROTECT)

    name = LocalizedField(related_name='ability_name', on_delete=models.CASCADE)
    description = LocalizedField(related_name='ability_description', on_delete=models.CASCADE)
    
    type =  models.ForeignKey(AbilityType, related_name='ability_type', on_delete=models.PROTECT)
    
    projectile = models.ForeignKey(Projectile, related_name='abilities', null=True, blank=True, on_delete=models.SET_NULL)

    is_self_ability = models.BooleanField(default=True)
    
    apply_damage = models.BooleanField(default=True)
    damage_type = models.ForeignKey(DamageType, related_name='ability_damage_type', on_delete=models.PROTECT)

    apply_knockback = models.BooleanField(default=False)
    is_inverse_knockback = models.BooleanField(default=False)
    knockback_force = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])
    knockback_duration = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])

    apply_stun = models.BooleanField(default=False)
    stun_chance = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    stun_duration = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(0.1), MaxValueValidator(3)]) 

    is_chargeable = models.BooleanField(default=False)
    charge_time = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    locked_icon_path = models.TextField(null=True, blank=True, default="")
    unlocked_icon_path = models.TextField(null=True, blank=True, default="")

    ability_state_duration = models.FloatField(null=False, blank=False, default=0.1, validators=[MinValueValidator(0.1), MaxValueValidator(2)])
    ability_animation_index = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])

    physical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    magical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])

    buff_health_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    buff_mana_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    buff_stamina_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])

    buff_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    buff_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    buff_stamina_regen_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])

    nerf_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)]) 
    nerf_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)]) 
    extra_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)]) 
    extra_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(1)]) 

    give_flat_health = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    give_flat_mana = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    give_flat_stamina = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    health_cost = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    mana_cost = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    stamina_cost = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    @classmethod
    def extra_process(cls, ability_element, data):
        data['type'] = ability_element.type.key
        data['ability_tree'] = ability_element.ability_tree.key        
        data['projectile'] = ability_element.projectile.key if ability_element.projectile is not None else None
        data['damage_type'] = ability_element.damage_type.key

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [Ability.name, Ability.description], cls.extra_process)
 
class Condition(BaseModel):
    prefix = 'condition_'
    use_identifier =  models.BooleanField(default=False, help_text="si es True, se usa la Key Al exportar a JSON. Caso contrario se usa identifier.")

    def to_dict_item(self):
        return self.identifier if self.use_identifier else self.key

class DialogItemsRequired(models.Model):
    dialogue = models.ForeignKey('Dialogue', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    def __str__(self):
        return f'Dialogue: {self.dialogue.key} - Item: {self.item.key} - Amount: {self.amount}'

    def to_dict_item(self):
        return {
            "ID": self.item.key,
            "Quantity": self.amount,
        }

class DialogItemsToRemove(models.Model):
    dialogue = models.ForeignKey('Dialogue', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    def __str__(self):
        return f'Dialogue: {self.dialogue.key} - Item: {self.item.key} - Amount: {self.amount}' 

    def to_dict_item(self):
        return {
            "ID": self.item.key,
            "Quantity": self.amount,
        }

class DialogItemsToGive(models.Model):
    dialogue = models.ForeignKey('Dialogue', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    def __str__(self):
        return f'Dialogue: {self.dialogue.key} - Item: {self.item.key} - Amount: {self.amount}' 

    def to_dict_item(self):
        return {
            "ID": self.item.key,
            "Quantity": self.amount,
        }

class DialogueTypes(models.TextChoices):
    BASIC = 'basic', 'Basic'
    QUEST_PROMPT = 'quest_prompt', 'Quest_Prompt'
    QUEST_END = 'quest_end', 'Quest_End'


def get_item_amount(items_queryset):
    item_list = []

    for item in items_queryset:
        item_list.append({
            'key': item.item.key,
            'amount': item.amount
        })

    return item_list

class Dialogue(BaseModel):
    prefix = 'dialogue_'

    npc = models.ForeignKey(NPC, related_name='dialogues', on_delete=models.CASCADE)

    type = models.CharField(max_length=20, null=False, blank=False, choices=DialogueTypes.choices)
    
    button_text = LocalizedField(related_name='dialogue_button_text_name', on_delete=models.CASCADE)

    appear_conditions = models.ManyToManyField(Condition, related_name='dialogues_to_appear', blank=True)
    no_appear_conditions = models.ManyToManyField(Condition, related_name='dialogues_to_no_appear', blank=True)
    trigger_id_conditions = models.ManyToManyField(Condition, related_name='ids_to_trigger', blank=True)
    trigger_diary_conditions = models.ManyToManyField(Condition, related_name='diaries_to_trigger', blank=True)

    required_items = models.ManyToManyField(Item, through=DialogItemsRequired, related_name='required_by_dialogues', blank=True)
    remove_items = models.ManyToManyField(Item, through=DialogItemsToRemove, related_name='removed_by_dialogues', blank=True)
    give_items = models.ManyToManyField(Item, through=DialogItemsToGive, related_name='given_by_dialogues', blank=True)

    #TODO: Crear Dialogos prompt y end al crear una quest.
    @classmethod
    def process_subtype(cls, subtype, dialogue_element, data):
        data['npc'] = dialogue_element.npc.key

        data["appear_conditions"] = [ac.key for ac in dialogue_element.appear_conditions.all()]
        data["no_appear_conditions"] = [nac.key for nac in dialogue_element.no_appear_conditions.all()]
        data["trigger_conditions"] = [tc.key for tc in dialogue_element.trigger_conditions.all()]

        data["required_items"] = get_item_amount(dialogue_element.dialogitemsrequired_set.select_related('item'))
        data["remove_items"] = get_item_amount(dialogue_element.dialogitemstoremove_set.select_related('item'))
        data["give_items"] = get_item_amount(dialogue_element.dialogitemstogive_set.select_related('item'))

        # Obtengo el subtype asociado al item
        reverse_name = subtype.dialogue.field.related_query_name()

        # Convierto el subtype a dict
        element_data = getattr(dialogue_element, reverse_name).to_dict()

        data.update(element_data)
    
    @classmethod
    def to_dict(cls, subtype):
        extra_process_by_subtype = lambda element, data: cls.process_subtype(subtype, element, data)
        return super().to_dict(None, [Dialogue.button_text], extra_process_by_subtype, type=subtype.type)

    @classmethod
    def to_dict2(cls):
        return (
            super().to_dict2("NormalDialogues", Dialogue.button_text, type=Basic.type) | 
            super().to_dict2("QuestsStartDialogues", Dialogue.button_text, type=QuestPrompt.type) |
            super().to_dict2("QuestsFinishDialogues", Dialogue.button_text, type=QuestEnd.type)
        )

    def to_dict_item(self):
        if self.type == DialogueTypes.BASIC:
            dialog_subtype = self.get_related_one_to_one(related_name="basic_dialogue")
        
        elif self.type == DialogueTypes.QUEST_PROMPT:
            dialog_subtype = self.get_related_one_to_one(related_name="quest_prompt_dialogue")

        elif self.type == DialogueTypes.QUEST_END:
            dialog_subtype = self.get_related_one_to_one(related_name="quest_end_dialogue")

        return {
            "DialogueID": self.key,
            "ButtonTextLocalizedKey": self.button_text.key,
            "ConditionsAndTriggers": {
                "AppearConditions": self.get_related_objects(related_name="appear_conditions"),
                "NotAppearConditions": self.get_related_objects(related_name="no_appear_conditions"),
                "TriggerCompletitionsIDs": self.get_related_objects(related_name="trigger_id_conditions"),
                "TriggerDiaryEntriesIDs": self.get_related_objects(related_name="trigger_diary_conditions"),
                "RequiredItems": self.get_related_objects("dialogitemsrequired_set", "item"),
            },
            "RemoveItems": self.get_related_objects("dialogitemstoremove_set", "item"),
            "AddItems": self.get_related_objects("dialogitemstogive_set", "item"),

        } | dialog_subtype

class DialogueSubtype(models.Model):
    type = None
    dialogue = models.OneToOneField(Dialogue, on_delete=models.CASCADE, related_name="dialogue_subtype")

    def __str__(self):
        return self.dialogue.key

    class Meta:
        abstract = True
    
    def to_dict(self, *fields_to_convert):
        fields = {}

        data = model_to_dict(self)

        # En Unity no usamos ids sino las keys de los items.
        data.pop('id')

        # No necesito la referencia al Dialogue.
        data.pop('dialogue')

        for field in fields_to_convert:
            field_name = field.field.name
            data[field_name] = getattr(self, field_name).key

        fields.update(data)

        return fields
    
    def get_related_one_to_one(self, related_name):
        """
        Devuelve la instancia de un modelo relacionado por related_name en un 1 to 1.
        """
        related_object = getattr(self, related_name)
        result = related_object.to_dict_item()
        return result

class DialogueSingleItem(BaseModel):
    prefix = 'dialoguesingleitem_'
    text = LocalizedField(related_name='dialogue_single_item_text', on_delete=models.CASCADE)
    speaker = models.BooleanField(default=True, help_text="False es NPC, True es Player.")

    def to_dict_item(self):
        return {
            "IsPlayer": self.speaker,
            "LocalizedTextKey":self.text.key,
        }

class DialogueSequenceItem(BaseModel):
    prefix = 'dialoguesequenceitem_'
    text = LocalizedField(related_name='dialogue_sequence_item_text', on_delete=models.CASCADE)
    speaker = models.BooleanField(default=True, help_text="False es NPC, True es Player.")
    index = models.PositiveIntegerField(default=1, help_text='Orden del diálogo', validators=[MinValueValidator(1), MaxValueValidator(1000)])
    sequence = models.ForeignKey('DialogueSequence', related_name='items', on_delete=models.CASCADE)

    def to_dict(self):
        fields = {}

        data = model_to_dict(self)

        # En Unity no usamos ids sino las keys de los items.
        data.pop('id')

        # No necesito la referencia al sequence.
        data.pop('sequence')

        field_name = DialogueSequenceItem.text.field.name
        data[field_name] = getattr(self, field_name).key

        fields.update(data)

        return fields
    
    def to_dict_item(self):
        return {
            "Index": self.index,
            "IsPlayer": self.speaker,
            "LocalizedTextKey": self.text.key,
        }

#TODO: Revisar si se puede omitir o hacer automatico este modelo
class DialogueSequence(BaseModel):
    prefix = 'dialoguesequence_'

    def to_dict_item(self):
        return self.get_related_objects(related_name="items", sort_lambda_key="Index")

class Basic(DialogueSubtype):
    type = DialogueTypes.BASIC
    dialogue = models.OneToOneField(Dialogue, on_delete=models.CASCADE, related_name="basic_dialogue")

    is_first_talk = models.BooleanField(default=False)
    is_one_shot = models.BooleanField(default=False) 
    sequence = models.OneToOneField(DialogueSequence, related_name='basic_dialogue_sequence', on_delete=models.CASCADE)

    def to_dict(self):
        fields = super().to_dict()

        fields['sequence'] = [sequence_item.to_dict() for sequence_item in self.sequence.items.all()]
        fields['sequence'].sort(key=lambda item: item['index'])
        return fields

    def to_dict_item(self):
        return {
            "IsOneShot": self.is_one_shot,
            "IsFirstTalk": self.is_first_talk,
            "DialogueSequence": self.get_related_one_to_one("sequence"),
        }

class QuestPrompt(DialogueSubtype):
    type = DialogueTypes.QUEST_PROMPT
    dialogue = models.OneToOneField(Dialogue, on_delete=models.CASCADE, related_name="quest_prompt_dialogue")

    text = models.OneToOneField(DialogueSingleItem, on_delete=models.CASCADE, related_name="quest_prompt_dialogue_text")
    deny_text = models.OneToOneField(DialogueSingleItem, on_delete=models.CASCADE, related_name="quest_prompt_dialogue_deny_text")
    acccept_text = models.OneToOneField(DialogueSingleItem, on_delete=models.CASCADE, related_name="quest_prompt_dialogue_accept_text")

    quest = models.OneToOneField(Quest, on_delete=models.CASCADE, related_name="quest_prompt_dialogue_quest")

    def to_dict_item(self):
        return {
            "QuestID": self.quest.key,
            "Dialogue": self.get_related_one_to_one("text"),
            "AcceptQuestDialogue": self.get_related_one_to_one("acccept_text"),
            "DeclineQuestDialogue": self.get_related_one_to_one("deny_text"),
        }

class QuestEnd(DialogueSubtype):
    type = DialogueTypes.QUEST_END
    dialogue = models.OneToOneField(Dialogue, on_delete=models.CASCADE, related_name="quest_end_dialogue")

    sequence = models.OneToOneField(DialogueSequence, related_name='quest_end_dialogue_sequence', on_delete=models.CASCADE)

    quest = models.OneToOneField(Quest, on_delete=models.CASCADE, related_name="quest_end_dialogue_quest")

    def to_dict(self):
        fields = super().to_dict()
        fields['sequence'] = [sequence_item.to_dict() for sequence_item in self.sequence.items.all()]
        fields['sequence'].sort(key=lambda item: item['index'])
        return fields

    def to_dict_item(self):
        return {
            "QuestID": self.quest.key,
            "DialogueSequence": self.get_related_one_to_one("sequence"),
        }

class DiaryPage(BaseModel):
    prefix = 'diarypage_'
    name = LocalizedField(related_name='diarypage_name', on_delete=models.CASCADE)
    appear_conditions = models.ManyToManyField(Condition, related_name='diarypage_to_appear', blank=True)
    
    @classmethod
    def extra_process(cls, diary_page_element, data):
        data["appear_conditions"] = [dp.key for dp in diary_page_element.appear_conditions.all()]
        data["diary_entries"] = [dpe.key for dpe in diary_page_element.entries.all()]

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [DiaryPage.name], extra_process=cls.extra_process)
    
    @classmethod
    def to_dict2(cls):
        return super().to_dict2("DiaryPages", DiaryPage.name)

    def to_dict_item(self):
        return {
            "PageID": self.key,
            "TitleTextKey": self.name.key,
            "AppearConditions": self.get_related_objects(related_name="appear_conditions"),
            "PageEntries": self.get_related_objects(related_name="entries"),
        }

class DiaryEntry(BaseModel):
    prefix = 'diaryentry_'
    title = LocalizedField(related_name='diaryentry_title', on_delete=models.CASCADE)
    text = LocalizedField(related_name='diaryentry_text', on_delete=models.CASCADE)
    appear_conditions = models.ManyToManyField(Condition, related_name='diaryentry_to_appear', blank=True)
    diary_page = models.ForeignKey(DiaryPage, related_name='entries', on_delete=models.CASCADE)

    @classmethod
    def extra_process(cls, diary_entry_element, data):
        data["appear_conditions"] = [de.key for de in diary_entry_element.appear_conditions.all()]

    @classmethod
    def to_dict(cls):
        return super().to_dict([DiaryEntry.diary_page], [DiaryEntry.title, DiaryEntry.text], extra_process=cls.extra_process)

    def to_dict_item(self):
        return {
            "AppearConditions": self.get_related_objects("appear_conditions"),
            "EntryID": self.key,
            "EntryTitleKey": self.title.key,
            "EntryTextKey": self.text.key,
        }

# Set Plural names
models_list = [
    (Item, 'Items'),
    (Weapon, 'Weapons'),
    (NPC, 'NPCs'),
    (Quest, 'Quests'),
    (AbilityTree, 'Ability Trees'),
    (Ability, 'Abilities'),
    (Projectile, 'Projectiles'),
    (POI, 'POIs'),
    (Dialogue, 'Dialogues'),
    (DialogueSequence, 'Dialogue Sequences'),
    (DialogueSingleItem, 'Dialogue Single Items'),
    (DialogueSequenceItem, 'Dialogue Sequence Items'),
    (DiaryPage, 'Diary Pages'),
    (DiaryEntry, 'Diary Entries'),
    (Condition, 'Conditions'),
    (LoadingScreenMessage, 'Loading Screen Messages'),
    (AttackSequence, 'Attack Sequences'),
    (QuestObjective, 'Quest Objectives'),
    (ItemReward, 'Item Rewards'),
    (AbilityType, 'Ability Types'),
    (ProjectileType, 'Projectile Types'),
    (WeaponType, 'Weapon Types'), 
    (DamageType, 'Damage Types'),
    (EquipmentType, 'Equipment Types'),
    (Localization, 'Localizations'),
    (Rarity, 'Rarities'), 
    # (Consumable, 'Consumables'),
    # (Equipment, 'Equipment'), 
    # (QuestItem, 'Quest Items'), 
    # (Basic, 'Basic Dialogues'),
    # (QuestPrompt, 'Quest Prompt Dialogues'),
    # (QuestEnd, 'Quest End Dialogues'),
    # (DialogItemsRequired, 'Dialogue Items Required'),
    # (DialogItemsToRemove, 'Dialogue Items to Remove'),
    # (DialogItemsToGive, 'Dialogue Items to Give'),
]

for i, model in enumerate(models_list, start=1):
    model[0]._meta.verbose_name_plural = f"{i}. {model[1]}"