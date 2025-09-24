// Evento para refrescar la seleccion de grilla cuando cambia el tipo de Dialogo.
const dialogueSubtypeChange = new CustomEvent("dialogueSubtypeChange");

document.addEventListener('DOMContentLoaded', function () {
    const typeField = document.querySelector('.form-row.field-type #id_type');
    const typeFieldReadOnly = document.querySelector('.form-row.field-type div.readonly');

    // IDs de los bloques inline
    const inlineGroups = {
        basic: document.getElementById('basic_dialogue-group'),
        quest_prompt: document.getElementById('quest_prompt_dialogue-group'),
        quest_end: document.getElementById('quest_end_dialogue-group'),
    };

    // Agrega required al inline activo
    function setFieldRequired(container, required) {
        if (!container) return;
        const inputs = container.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (required) {
                input.setAttribute('required', 'required');
            } else {
                input.removeAttribute('required');
            }
        });
    }

    function updateInlines(value) {
        const selected = value;

        for (const [key, div] of Object.entries(inlineGroups)) {
            if (!div) continue;

            const shouldShow = key === selected;
            div.style.display = shouldShow ? 'block' : 'none';

            // Marca o desmarca campos como requeridos
            setFieldRequired(div, shouldShow);
        }
    }

    if (typeField) {
        typeField.addEventListener('change',() => {
            updateInlines(typeField.value);
            
            // Eliminar los formularios de tipo de item que no correspondan.
            const basicDialogueDeleteButton = document.querySelector('#basic_dialogue-0 a.inline-deletelink');
            const questPromptDialogueDeleteButton = document.querySelector('#quest_prompt_dialogue-0 a.inline-deletelink');
            const questEndDeleteButton = document.querySelector('#quest_end_dialogue-0 a.inline-deletelink');

            // agregar el que si corresponda.
            const basicDialogueAddButton = document.querySelector('#basic_dialogue-group a.addlink');
            const questPromptAddButton = document.querySelector('#quest_prompt_dialogue-group a.addlink');
            const questEndAddButton = document.querySelector('#quest_end_dialogue-group a.addlink');

            const addAndDeleteButtons = {
                'basic': {
                    'delete':basicDialogueDeleteButton, 
                    'add': basicDialogueAddButton,
                },

                'quest_prompt': {
                    'delete':questPromptDialogueDeleteButton,
                    'add':questPromptAddButton
                },

                'quest_end': {
                    'delete': questEndDeleteButton,
                    'add': questEndAddButton
                },
            };

            Object.keys(addAndDeleteButtons).forEach(function(button) {              
                // Borrar los que no corresponden
                if(addAndDeleteButtons[button]['delete'] && button.toLowerCase() != typeField.value.toLowerCase())
                    addAndDeleteButtons[button]['delete'].dispatchEvent(new Event("click", { bubbles: true }));

                // Agregar el correspondiente
                if(!addAndDeleteButtons[button]['delete'] && button.toLowerCase() == typeField.value.toLowerCase())
                    addAndDeleteButtons[button]['add'].dispatchEvent(new Event("click", { bubbles: true }));
            });

            // Despacho el evento para que el selector de grilla se refresque.
            document.dispatchEvent(dialogueSubtypeChange);
        });
        updateInlines(typeField.value); // Inicializa al cargar la página

    }else if(typeFieldReadOnly){
        updateInlines(typeFieldReadOnly.innerHTML.toLocaleLowerCase());
    }
});