function updateQuestObjectiveKey(identifierInput, keyInput, indexInput, addRelatedLink) {
    getSanitizedKey(keyInput, "QuestObjective", {
        "prefix": identifierInput.dataset.keyPrefix,
        "quest_key": document.querySelector('#id_key').value,
        "slug": identifierInput.value,
        "quest_objective_index": indexInput.value,
    },
        (updatedKey) => {
            // Update popup link
            if (addRelatedLink) {
                const baseUrl = addRelatedLink.getAttribute('href').split('?')[0];
                const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(updatedKey + "_brief")}`;
                addRelatedLink.setAttribute('href', newHref);
            }
        }
    )
}

function updateQuestObjectives(container) {
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
            identifierInput.addEventListener('input', e => {
                updateQuestObjectiveKey(identifierInput, keyInput, indexInput, addRelatedLink);
            });

            indexInput.addEventListener('input', e => {
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
    document.querySelector('#id_identifier').addEventListener('input', e => {
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