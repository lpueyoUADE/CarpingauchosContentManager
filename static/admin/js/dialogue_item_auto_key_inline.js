function updateDialogueSequenceItemKey(identifierInput, keyInput, indexInput, addRelatedLink) {
    const prefix = identifierInput.dataset.keyPrefix || '';
    const raw = identifierInput.value;

    const slug = raw
        .toLowerCase()
        .replace(/[^\w\s]/g, '')  // elimina caracteres especiales
        .trim()
        .replace(/\s+/g, '_');   // reemplaza espacios por guiones bajos

    dialogue_item_key = document.querySelector('#id_key').value; // key del sequence item
    dialogue_item_index = indexInput.value;

    finalValue = prefix + slug + "_" + dialogue_item_key + "_" + dialogue_item_index; 

    keyInput.value = finalValue;

    // Update popup link
    if (addRelatedLink) {
        const baseUrl = addRelatedLink.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(finalValue + "_text")}`;
        addRelatedLink.setAttribute('href', newHref);
    }
}

function updateDialogueSequenceItems(container){
    const rows = container.querySelectorAll('[id^="items-"]');
     rows.forEach(row => {
        const identifierInput = row.querySelector('input[id$="-identifier"]');
        const keyInput = row.querySelector('input[id$="-key"]');
        const indexInput = row.querySelector('input[id$="-index"]');
        const addRelatedLink = row.querySelector('a.related-widget-wrapper-link.add-related');

        if (identifierInput && keyInput && indexInput) {
            updateDialogueSequenceItemKey(identifierInput, keyInput, indexInput, addRelatedLink);
        }
     });
}

function setupInlineKeyAutoFill(container) {
    const rows = container.querySelectorAll('[id^="items-"]');

    rows.forEach(row => {
        const identifierInput = row.querySelector('input[id$="-identifier"]');
        const keyInput = row.querySelector('input[id$="-key"]');
        const indexInput = row.querySelector('input[id$="-index"]');
        const addRelatedLink = row.querySelector('a.related-widget-wrapper-link.add-related');

        if (identifierInput && keyInput && indexInput) {
            identifierInput.addEventListener('input', () => {
                updateDialogueSequenceItemKey(identifierInput, keyInput, indexInput, addRelatedLink);
            });

            indexInput.addEventListener('input', () => {
                updateDialogueSequenceItemKey(identifierInput, keyInput, indexInput, addRelatedLink);
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('#items-group');
    if (container) {
        setupInlineKeyAutoFill(container);
    }

    // Actualizar los quest objectives cuando cambia el item identifier.
    document.querySelector('#id_identifier').addEventListener('input', () => {
        updateDialogueSequenceItems(container);
    })

    // Detectar cuando se agrega un nuevo formset dinámicamente
    document.body.addEventListener('click', e => {
        if (e.target && e.target.classList.contains('addlink')) {
            setTimeout(() => {
                const container = document.querySelector('#items-group');
                if (container) {
                    setupInlineKeyAutoFill(container);
                }
            }, 100); // delay para asegurar que el DOM se actualice
        }
    });
});