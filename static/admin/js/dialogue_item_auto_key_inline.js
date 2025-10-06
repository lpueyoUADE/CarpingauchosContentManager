function updateDialogueSequenceItemKey(identifierInput, keyInput, indexInput, addRelatedLink) {
    getSanitizedKey(keyInput, "DialogueSequenceItem", {
        "prefix": identifierInput.dataset.keyPrefix,
        "dialogue_key": document.querySelector('#id_key').value,
        "slug": identifierInput.value,
        "dialogue_item_index": indexInput.value,
    }, (updatedKey) => {
        // Update popup link
        if (addRelatedLink) {
            const baseUrl = addRelatedLink.getAttribute('href').split('?')[0];
            const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(updatedKey + "_text")}`;
            addRelatedLink.setAttribute('href', newHref);
        }
    });
}

function updateDialogueSequenceItems(container) {
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