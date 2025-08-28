function updateDiaryEntryKey(identifierInput, keyInput, addTitleLink, addTextLink) {
    const prefix = identifierInput.dataset.keyPrefix || '';
    const raw = identifierInput.value;

    const slug = raw
        .toLowerCase()
        .replace(/[^\w\s]/g, '')  // elimina caracteres especiales
        .trim()
        .replace(/\s+/g, '_');   // reemplaza espacios por guiones bajos

    diary_page_key = document.querySelector('#id_key').value;

    finalValue = prefix + slug + "_" + diary_page_key; 

    keyInput.value = finalValue;

    // Update popup link
    if (addTitleLink) {
        const baseUrl = addTitleLink.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(finalValue + "_title")}`;
        addTitleLink.setAttribute('href', newHref);
    }

    if (addTextLink) {
        const baseUrl = addTextLink.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(finalValue + "_text")}`;
        addTextLink.setAttribute('href', newHref);
    }
}

function updateDiaryEntries(container){
    const rows = container.querySelectorAll('tr[id^="entries-"]');
     rows.forEach(row => {
        const identifierInput = row.querySelector('input[id$="-identifier"]');
        const keyInput = row.querySelector('input[id$="-key"]');
        const addTitleLink = row.querySelector('a[id^="add_"][id$="-title"]');
        const addTextLink = row.querySelector('a[id^="add_"][id$="-text"]');

        if (identifierInput && keyInput) {
            updateDiaryEntryKey(identifierInput, keyInput, addTitleLink, addTextLink);
        }

        identifierInput.addEventListener('input', () => {
            updateDiaryEntryKey(identifierInput, keyInput, addTitleLink, addTextLink);
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('#entries-group');
    if (container) {
        updateDiaryEntries(container);
    }

    // Actualizar los diary entries cuando cambia el diary page identifier.
    document.querySelector('#id_identifier').addEventListener('input', () => {
        updateDiaryEntries(container);
    })

    // Detectar cuando se agrega un nuevo formset dinámicamente
    document.body.addEventListener('click', e => {
        if (e.target && e.target.classList.contains('addlink')) {
            setTimeout(() => {
                const container = document.querySelector('#entries-group');
                if (container) {
                    updateDiaryEntries(container);
                }
            }, 100); // delay para asegurar que el DOM se actualice
        }
    });
});