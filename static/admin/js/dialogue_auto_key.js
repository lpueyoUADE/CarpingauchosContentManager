function isEditingForm() {
    const path = window.location.pathname;
    return path.includes('dialogue') && path.includes('change');
}

function updateKey(identifierInput, keyInput, npcSelect, typeSelect) {
    const prefix = identifierInput.dataset.keyPrefix || '';
    const slug = identifierInput.value
        .toLowerCase()
        .replace(/[^\w\s]/g, '')    // elimina caracteres no alfanuméricos
        .trim()
        .replace(/\s+/g, '_');      // reemplaza espacios por guiones bajos

    const npc = npcSelect.options[npcSelect.selectedIndex].text.split("_")[1];

    const typeValue = isEditingForm() ? typeSelect.innerText : typeSelect.value;
    keyInput.value = prefix + typeValue.toLowerCase() + "_" + npc + "_" + slug;
}

document.addEventListener('DOMContentLoaded', function () {
    const identifierInput = document.querySelector('#id_identifier');
    const keyInput = document.querySelector('#id_key');
    const typeSelect = isEditingForm() ? document.querySelector('.field-type .readonly') : document.querySelector('#id_type');
    const npcSelect = document.querySelector('#id_npc');

    if (identifierInput && keyInput && npcSelect && typeSelect) {
        updateKey(identifierInput, keyInput, npcSelect, typeSelect);
        
        typeSelect.addEventListener('input', function () {
            updateKey(identifierInput, keyInput, npcSelect, typeSelect);
        });

        npcSelect.addEventListener('input', function () {
            updateKey(identifierInput, keyInput, npcSelect, typeSelect);
        });

        identifierInput.addEventListener('input', function () {
            updateKey(identifierInput, keyInput, npcSelect, typeSelect);
        });
    }
});