function isEditingForm() {
    const path = window.location.pathname;
    return path.includes('item') && path.includes('change');
}

function updateKey(identifierInput, keyInput, raritySelect, typeSelect) {
    const prefix = identifierInput.dataset.keyPrefix || '';
    const slug = identifierInput.value;

    const rarity = raritySelect.options[raritySelect.selectedIndex].text.split("_")[1];

    const typeValue = isEditingForm() ? typeSelect.innerText : typeSelect.value;
    keyInput.value = prefix + typeValue + "_" + slug + "_" + rarity
    keyInput.value = keyInput.value.toLowerCase()
        .replace(/[^\w\s]/g, '')    // elimina caracteres no alfanuméricos
        .trim()
        .replace(/\s+/g, '_');      // reemplaza espacios por guiones bajos;
}

document.addEventListener('DOMContentLoaded', function () {
    const identifierInput = document.querySelector('#id_identifier');
    const keyInput = document.querySelector('#id_key');
    const typeSelect = isEditingForm() ? document.querySelector('.field-type .readonly') : document.querySelector('#id_type');
    const raritySelect = document.querySelector('#id_rarity');

    if (identifierInput && keyInput && raritySelect && typeSelect) {
        updateKey(identifierInput, keyInput, raritySelect, typeSelect);
        
        typeSelect.addEventListener('input', function () {
            updateKey(identifierInput, keyInput, raritySelect, typeSelect);
        });

        raritySelect.addEventListener('input', function () {
            updateKey(identifierInput, keyInput, raritySelect, typeSelect);
        });

        identifierInput.addEventListener('input', function () {
            updateKey(identifierInput, keyInput, raritySelect, typeSelect);
        });
    }
});