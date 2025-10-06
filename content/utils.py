import re

class KeyGenerator:
    fields = []
    format = "COMPLETE ME" # Por ejemplo: prefix_dialogue_key_slug_dialogue_item_index;
    processors = None

    @classmethod
    def _get_format(cls):
        return cls.format

    @classmethod
    def get_params_from_request(cls, request):
        params = {}

        for field in cls.fields:
            params[field] = request.GET.get(field)

        return params

    @classmethod
    def sanitize(cls, key):
        key = key.lower().strip().replace(" ", "_")
        re.sub(r"[^a-z0-9_]", "", key) # Borro caracteres que no sean alfanumericos.

        return key

    @classmethod
    def get_field_processors(cls):
        """
        Retorna un diccionario {field_name: method} para
        todos los métodos que empiecen con 'process_field_'
        """
        if cls.processors is None:
            cls.processors = {}

            for attr_name in dir(cls):
                if attr_name.startswith("process_field_"):
                    field_name = attr_name[len("process_field_"):]  # todo lo que viene después
                    method = getattr(cls, attr_name)
                    cls.processors[field_name] = method
        
        return cls.processors

    @classmethod
    def apply_processor(cls, field, value):
        if field in cls.get_field_processors():
            return cls.processors[field](value)
        
        return value

    @classmethod
    def generate_key(cls, **params):
        final_key = cls._get_format()

        for field in cls.fields:
            value = cls.apply_processor(field, params[field])
            final_key = final_key.replace(field, value)

        final_key = cls.sanitize(final_key)

        return final_key

class DialogueKeyGenerator(KeyGenerator):
    fields = [
        "prefix",
        "type",
        "npc",
        "slug"
    ]

    @classmethod
    def process_field_npc(cls, value):
        if "npc_" in value:
            return value.split("npc_")[1] # El texto se hace larguisimo asi que lo corto un poco.
        
        return ""

    format = f"{fields[0]}{fields[1]}_{fields[2]}_{fields[3]}"

class DialogueSequenceKeyGenerator(KeyGenerator):
    fields = [
        "slug"
    ]

    format = f"{fields[0]}"

class DialogueSequenceItemKeyGenerator(KeyGenerator):
    fields = [
        "prefix",
        "dialogue_key",
        "slug",
        "dialogue_item_index",
    ]

    @classmethod
    def process_field_dialogue_key(cls, value):
        return "_".join(value.split("_")[1:]) # El texto se hace larguisimo asi que lo corto un poco.

    format = f"{fields[0]}{fields[1]}_{fields[2]}_{fields[3]}"

class DialogueSingleItemKeyGenerator(KeyGenerator):
    fields = [
        "prefix",
        "slug",
        "suffix",
    ]

    format = f"{fields[0]}{fields[1]}_{fields[2]}"

class QuestObjectiveKeyGenerator(KeyGenerator):
    fields = [
        "prefix",
        "quest_key",
        "slug",
        "quest_objective_index",
    ]

    format = f"{fields[0]}{fields[1]}_{fields[2]}_{fields[3]}"

class DiaryEntryKeyGenerator(KeyGenerator):
    fields = [
        "prefix",
        "slug",
        "diary_page_key",
    ]

    format = f"{fields[0]}{fields[1]}_{fields[2]}"