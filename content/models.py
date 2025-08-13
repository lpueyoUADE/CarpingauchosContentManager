from django.db import models
from django.db.models import OneToOneField
from django.forms.models import model_to_dict
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import slugify

class BaseModel(models.Model):
    prefix = ''

    identifier =  models.CharField(max_length=150, unique=True, null=False, blank=False, help_text="Texto identificador del recurso.")
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

    name = models.OneToOneField(Localization, related_name='npc_name', on_delete=models.CASCADE)
    

class Quest(BaseModel):
    prefix = 'quest_'
    title = models.OneToOneField(Localization, related_name='quest_title', on_delete=models.CASCADE)
    brief = models.OneToOneField(Localization, related_name='quest_brief', on_delete=models.CASCADE)

    money_reward = models.PositiveIntegerField(default=0)
    ability_points_reward = models.PositiveIntegerField(default=0)
    
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

class QuestObjective(BaseModel):
    prefix = 'quest_objective_'

    index = models.PositiveIntegerField(default=1, help_text='Orden del objetivo')

    brief = models.OneToOneField(Localization, related_name='quest_objective_brief', on_delete=models.CASCADE)
    is_trackeable = models.BooleanField(default=True)
    
    quest = models.ForeignKey(Quest, related_name='objectives', on_delete=models.CASCADE)

    @classmethod
    def extra_process(cls, element, data):
        data['quest'] = element.quest.key

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [QuestObjective.brief], cls.extra_process)

#TODO: implementar todos los modelos.
"""
class Diary:
    pass

class Dialogue:
    pass

class DialogueSequence:
    pass

class Ability:
    pass
    
"""
class Rarity(BaseModel):
    prefix = 'rarity_'
    name = models.OneToOneField(Localization, related_name='rarity_name', on_delete=models.CASCADE)
    color = models.CharField(
        max_length=7,
        default="#FFFFFF",
        help_text="Color en formato hexadecimal, ej. #FF0000"
    )

    @classmethod
    def to_dict(cls):
        return super().to_dict([Rarity.color], [Rarity.name])

class ItemTypes(models.TextChoices):
    WEAPON = 'weapon', 'Weapon'
    EQUIPMENT = 'equipment', 'Equipment'
    CONSUMABLE = 'consumable', 'Consumable'
    QUEST = 'quest', 'Quest Item'

class Item(BaseModel):
    prefix = 'item_'

    name = models.OneToOneField(Localization, related_name='item_name', on_delete=models.CASCADE)
    description = models.OneToOneField(Localization, related_name='item_description', on_delete=models.CASCADE)

    rarity = models.ForeignKey(Rarity, related_name='item_rarity', on_delete=models.PROTECT)
    value =  models.PositiveIntegerField(default=0)

    icon_path = models.TextField(null=True, blank=True, default="")

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
    amount = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Quest: {self.quest.key} - Item: {self.item.key} - Amount: {self.amount}'

class Consumable(ItemSubtype):
    type = ItemTypes.CONSUMABLE
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="consumable_item")

    is_single_effect = models.BooleanField(default=True)
    cooldown = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    
    effect_Duration =  models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    
    physical_Resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    magical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    heal_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    mana_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    stamina_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    buff_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    buff_stamina_regen_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    nerf_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    nerf_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    extra_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    extra_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    give_flat_health = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    give_flat_mana = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    give_flat_stamina = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

class WeaponType(BaseModel):
    prefix = "weapon_type_"
    name = models.OneToOneField(Localization, related_name='weapon_type_name', on_delete=models.CASCADE)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [WeaponType.name])

class DamageType(BaseModel):
    prefix = "damage_type_"
    name = models.OneToOneField(Localization, related_name='damage_type_name', on_delete=models.CASCADE)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [DamageType.name])

class Weapon(ItemSubtype):
    type = ItemTypes.WEAPON
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="weapon_item")
    weapon_type = models.ForeignKey(WeaponType, related_name='weapon_type', on_delete=models.PROTECT) 
    damage_type = models.ForeignKey(DamageType, related_name='damage_type', on_delete=models.PROTECT)
 
    prefab = models.TextField(null=True, blank=True, default="")
    poise_break_force = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    flat_physical_damage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    flat_magical_damage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    physical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    magical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_health_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_mana_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_stamina_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_stamina_regen_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    nerf_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    nerf_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    extra_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    extra_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    attack_stamina_cost = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    def to_dict(self):
        return super().to_dict(Weapon.weapon_type, Weapon.damage_type)

class EquipmentType(BaseModel):
    prefix = "equipment_type_"
    name = models.OneToOneField(Localization, related_name='equipment_type_name', on_delete=models.CASCADE)

    @classmethod
    def to_dict(cls):
        return super().to_dict(None, [EquipmentType.name])

class Equipment(ItemSubtype):
    type = ItemTypes.EQUIPMENT

    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="equipment_item")
    equipment_type = models.ForeignKey(EquipmentType, related_name='equipment_type', on_delete=models.PROTECT)
    
    prefab = models.TextField(null=True, blank=True, default="")
    flat_physical_damage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    flat_magical_damage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])
    physical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    magical_resistance_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_health_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_mana_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_stamina_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    buff_stamina_regen_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    nerf_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    nerf_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    extra_physical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    extra_magical_damage_percentage = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]) 
    stamina_cost = models.FloatField(null=False, blank=False, default=0, validators=[MinValueValidator(0)])

    def to_dict(self):
        return super().to_dict(Equipment.equipment_type)

class QuestItem(ItemSubtype):
    type = ItemTypes.QUEST
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="quest_item")