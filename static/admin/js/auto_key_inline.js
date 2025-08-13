function updateQuestObjectiveKey(identifierInput, keyInput, indexInput, addRelatedLink) {
    const prefix = identifierInput.dataset.keyPrefix || '';
    const raw = identifierInput.value;

    const slug = raw
        .toLowerCase()
        .replace(/[^\w\s]/g, '')  // elimina caracteres especiales
        .trim()
        .replace(/\s+/g, '_');   // reemplaza espacios por guiones bajos

    quest_key = document.querySelector('#id_key').value; // key de la Quest
    quest_objective_index = indexInput.value;

    finalValue = prefix + slug + "_" + quest_key + "_" + quest_objective_index; 

    keyInput.value = finalValue;

    // Update popup link
    if (addRelatedLink) {
        const baseUrl = addRelatedLink.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(finalValue + "_brief")}`;
        addRelatedLink.setAttribute('href', newHref);
    }
}

function updateQuestObjectives(container){
    const rows = container.querySelectorAll('[id^="objectives-"]');
     rows.forEach(row => {
        const identifierInput = row.querySelector('input[id$="-identifier"]');
        const keyInput = row.querySelector('input[id$="-key"]');
        const indexInput = row.querySelector('input[id$="-index"]');
        const addRelatedLink = row.querySelector('a.related-widget-wrapper-link.add-related');

        if (identifierInput && keyInput && indexInput) {
            updateQuestObjectiveKey(identifierInput, keyInput, indexInput, addRelatedLink);
        }
     });
}

function setupInlineKeyAutoFill(container) {
    const rows = container.querySelectorAll('[id^="objectives-"]');

    rows.forEach(row => {
        const identifierInput = row.querySelector('input[id$="-identifier"]');
        const keyInput = row.querySelector('input[id$="-key"]');
        const indexInput = row.querySelector('input[id$="-index"]');
        const addRelatedLink = row.querySelector('a.related-widget-wrapper-link.add-related');

        if (identifierInput && keyInput && indexInput) {
            identifierInput.addEventListener('input', () => {
                updateQuestObjectiveKey(identifierInput, keyInput, indexInput, addRelatedLink);
            });

            indexInput.addEventListener('input', () => {
                updateQuestObjectiveKey(identifierInput, keyInput, indexInput, addRelatedLink);
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('#objectives-group');
    if (container) {
        setupInlineKeyAutoFill(container);
    }

    // Actualizar los quest objectives cuando cambia el quest identifier.
    document.querySelector('#id_identifier').addEventListener('input', () => {
        updateQuestObjectives(container);
    })

    // Detectar cuando se agrega un nuevo formset dinámicamente
    document.body.addEventListener('click', e => {
        if (e.target && e.target.classList.contains('addlink')) {
            setTimeout(() => {
                const container = document.querySelector('#objectives-group');
                if (container) {
                    setupInlineKeyAutoFill(container);
                }
            }, 100); // delay para asegurar que el DOM se actualice
        }
    });
});