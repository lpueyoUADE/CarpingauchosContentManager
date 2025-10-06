from django.http import JsonResponse
from .utils import DialogueKeyGenerator as dKeyGenerator
from .utils import DialogueSequenceKeyGenerator as dSequenceKeyGenerator
from .utils import DialogueSequenceItemKeyGenerator as dSequenceItemKeyGenerator
from .utils import DialogueSingleItemKeyGenerator as dSingleItemKeyGenerator
from .utils import QuestObjectiveKeyGenerator as qoKeyGenerator
from .utils import DiaryEntryKeyGenerator as deKeyGenerator

def _generate_key(keygen, request):
    return keygen.generate_key(**keygen.get_params_from_request(request))

def generate_key(request, model):
    key = ""

    match model:
        case "Dialogue":
            key = _generate_key(dKeyGenerator, request)
    
        case "DialogueSequence":
            key = _generate_key(dSequenceKeyGenerator, request)
    
        case "DialogueSequenceItem":
            key = _generate_key(dSequenceItemKeyGenerator, request)

        case "DialogueSingleItem":
            key = _generate_key(dSingleItemKeyGenerator, request)
        
        case "QuestObjective":
            key = _generate_key(qoKeyGenerator, request)
        
        case "DiaryEntry":
            key = _generate_key(deKeyGenerator, request)

        case _:
            raise NotImplementedError("Modelo desconocido: ", model)

    return JsonResponse({
        "key": key
    })