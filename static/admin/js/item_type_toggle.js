// Evento para refrescar la seleccion de grilla cuando cambia el tipo.
const itemSubtypeChange = new CustomEvent("itemSubtypeChange");

document.addEventListener('DOMContentLoaded', function () {
    const typeField = document.querySelector('.form-row.field-type #id_type');
    const typeFieldReadOnly = document.querySelector('.form-row.field-type div.readonly');

    // IDs de los bloques inline
    const inlineGroups = {
        weapon: document.getElementById('weapon_item-group'),
        equipment: document.getElementById('equipment_item-group'),
        consumable: document.getElementById('consumable_item-group'),
        quest: document.getElementById('quest_item-group'),
    };

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
            const consumableDeleteButton = document.querySelector('#consumable_item-0 a.inline-deletelink');
            const weaponDeleteButton = document.querySelector('#weapon_item-0 a.inline-deletelink');
            const equipmentDeleteButton = document.querySelector('#equipment_item-0 a.inline-deletelink');
            const questitemDeleteButton = document.querySelector('#quest_item-0 a.inline-deletelink');

            // agregar el que si corresponda.
            const consumableAddButton = document.querySelector('#consumable_item-group a.addlink');
            const weaponAddButton = document.querySelector('#weapon_item-group a.addlink');
            const equipmentAddButton = document.querySelector('#equipment_item-group a.addlink');
            const questitemAddButton = document.querySelector('#quest_item-group a.addlink');

            const addAndDeleteButtons = {
                'consumable': {
                    'delete':consumableDeleteButton, 
                    'add': consumableAddButton,
                },

                'weapon': {
                    'delete':weaponDeleteButton,
                    'add':weaponAddButton
                },

                'equipment':{
                    'delete': equipmentDeleteButton,
                    'add': equipmentAddButton
                },
                'quest': {
                    'delete': questitemDeleteButton,
                    'add': questitemAddButton
                }
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
            document.dispatchEvent(itemSubtypeChange);
        });
        updateInlines(typeField.value); // Inicializa al cargar la página

    }else if(typeFieldReadOnly){
        updateInlines(typeFieldReadOnly.innerHTML.toLocaleLowerCase());
    }
});