from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db import transaction
from django.apps import apps
from .utils import DialogueKeyGenerator as dKeyGenerator
from .utils import DialogueSequenceKeyGenerator as dSequenceKeyGenerator
from .utils import DialogueSingleItemKeyGenerator as dSingleItemKeyGenerator
from .models import (
    Localization,
    Quest,
    QuestObjective,
    Condition,
    Dialogue,
    DialogueTypes,
    DialogueSequence,
    DialogueSingleItem,
    QuestPrompt,
    QuestEnd,
)

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

@receiver(post_save, sender=Quest)
def crear_quest(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta cada vez que se guarda un MiModelo.
    - sender: el modelo que dispara la señal (MiModelo en este caso).
    - instance: la instancia recién creada/guardada.
    - created: True si es una nueva instancia, False si es una actualización.
    """
    if created:  # Solo la primera vez que se guarda
        # Cuando inicia una quest se triggerea su ID
        quest_key = instance.key
        quest_stared_condition = Condition.objects.create(
            identifier= f"{quest_key}",
            key= f"condition_{quest_key}",
            use_identifier=True,
        )

        # Condicion de Quest Finalizada
        quest_ended_condition = Condition.objects.create(
            identifier= f"{quest_key}_finished",
            key= f"condition_{quest_key}_finished",
            use_identifier=True,
        )

        # Dialogue Prompt
        dialogue_prompt_key = dKeyGenerator.generate_key(
            prefix=Dialogue.prefix,
            type=DialogueTypes.QUEST_PROMPT,
            npc=instance.npc_giver.key,
            slug=quest_key
        )

        button_text_loc = Localization.objects.create(
            identifier = f"{dialogue_prompt_key}_button_text",
            key= f"loc_{dialogue_prompt_key}_button_text",
            english="COMPLETAR button Text de " + dialogue_prompt_key,
            spanish="COMPLETAR button Text de" + dialogue_prompt_key,
        )

        dialogue = Dialogue.objects.create(
            identifier = quest_key,
            key= dialogue_prompt_key,
            npc = instance.npc_giver,
            type = DialogueTypes.QUEST_PROMPT,
            button_text = button_text_loc
        )

        dialogue.no_appear_conditions.add(quest_stared_condition)

        # Quest Prompt dialogue subtype
        # Text
        singleitem_text_key = dSingleItemKeyGenerator.generate_key(
            prefix = DialogueSingleItem.prefix,
            slug = dialogue_prompt_key,
            suffix = 'single_item'
        )

        singleitem_text_loc = Localization.objects.create(
            identifier = f"{singleitem_text_key}_text",
            key= f"loc_{singleitem_text_key}_text",
            english="COMPLETAR dialogue single item text de " + singleitem_text_key,
            spanish="COMPLETAR dialogue single item text de " + singleitem_text_key,
        )

        singleitem_text = DialogueSingleItem.objects.create(
            identifier = f"{dialogue_prompt_key}_single_item",
            key= singleitem_text_key,
            text = singleitem_text_loc,
            speaker = False,
        )

        # Deny Text
        singleitem_deny_text_key = dSingleItemKeyGenerator.generate_key(
            prefix = DialogueSingleItem.prefix,
            slug = dialogue_prompt_key,
            suffix = 'deny_single_item'
        )

        singleitem_deny_text_loc = Localization.objects.create(
            identifier = f"{singleitem_deny_text_key}_text",
            key= f"loc_{singleitem_deny_text_key}_text",
            english="COMPLETAR dialogue deny single item text de " + singleitem_deny_text_key,
            spanish="COMPLETAR dialogue deny single item text de " + singleitem_deny_text_key,
        )

        singleitem_deny_text = DialogueSingleItem.objects.create(
            identifier = f"{dialogue_prompt_key}_deny_single_item",
            key= singleitem_deny_text_key,
            text = singleitem_deny_text_loc,
            speaker = True,
        )

        # Accept Text
        singleitem_accept_text_key = dSingleItemKeyGenerator.generate_key(
            prefix = DialogueSingleItem.prefix,
            slug = dialogue_prompt_key,
            suffix = 'accept_single_item'
        )

        singleitem_accept_text_loc = Localization.objects.create(
            identifier = f"{singleitem_accept_text_key}_text",
            key= f"loc_{singleitem_accept_text_key}_text",
            english="COMPLETAR dialogue accept single item text de " + singleitem_accept_text_key,
            spanish="COMPLETAR dialogue accept single item text de " + singleitem_accept_text_key,
        )

        singleitem_accept_text = DialogueSingleItem.objects.create(
            identifier = f"{dialogue_prompt_key}_accept_single_item",
            key= singleitem_accept_text_key,
            text = singleitem_accept_text_loc,
            speaker = True,
        )

        QuestPrompt.objects.create(
            dialogue = dialogue,
            text = singleitem_text,
            deny_text = singleitem_deny_text,
            acccept_text = singleitem_accept_text,
            quest = instance
        )

        # Quest End
        dialogue_end_key = dKeyGenerator.generate_key(
            prefix=Dialogue.prefix,
            type=DialogueTypes.QUEST_END,
            npc=instance.npc_giver.key,
            slug=quest_key
        )
        end_button_text_loc = Localization.objects.create(
            identifier = f"{dialogue_end_key}_button_text",
            key= f"loc_{dialogue_end_key}_button_text",
            english="COMPLETAR button Text de " + dialogue_end_key,
            spanish="COMPLETAR button Text de" + dialogue_end_key,
        )

        dialogue_end = Dialogue.objects.create(
            identifier = quest_key,
            key= dialogue_end_key,
            npc = instance.npc_giver,
            type = DialogueTypes.QUEST_END,
            button_text = end_button_text_loc
        )

        # Dialogue end Conditions
        dialogue_end.appear_conditions.add(quest_stared_condition)
        dialogue_end.no_appear_conditions.add(quest_ended_condition)
        dialogue_end.trigger_id_conditions.add(quest_ended_condition)

        dialogue_sequence_end_key = dSequenceKeyGenerator.generate_key(
            slug=dialogue_end_key
        )

        print(dialogue_end_key)
        # Dialogue Sequence
        dialogue_sequence_end = DialogueSequence.objects.create(
            identifier = dialogue_end_key,
            key = dialogue_sequence_end_key,
        )

        # Dialogue Quest End
        QuestEnd.objects.create(
            dialogue = dialogue_end,
            sequence = dialogue_sequence_end,
            quest = instance
        )

        # Asocio la condición del anteultimo questobjective al appear conditions del quest end
        # Definimos una acción diferida para después del commit
        def link_conditions_after_commit():
            all_conditions = Condition.objects.filter(identifier__contains=quest_key).order_by('identifier')

            # Me quedo con la anteultima condicion, o la primera si es una sola.
            dialogue_end.appear_conditions.add(all_conditions[len(all_conditions) -2] if len(all_conditions) > 1 else all_conditions[0])

        transaction.on_commit(link_conditions_after_commit)
    
@receiver(post_save, sender=QuestObjective)
def crear_quest_objectives(sender, instance, created, **kwargs):
    if created:
        key = instance.key

        # Quest objectives
        Condition.objects.create(
            identifier= f"{key}",
            key= f"condition_{key}",
            use_identifier=True,
        )  


# Se ejecuta cuando Django carga las apps
auto_register_post_deletes()