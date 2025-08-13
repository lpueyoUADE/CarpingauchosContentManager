function updateHref(anchor, fieldName) {
    if (anchor) {
        key = document.querySelector('#id_key').value;
        const baseUrl = anchor.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(key + "_" + fieldName)}`;
        anchor.setAttribute('href', newHref);
    }
}

function isEditingForm() {
    const path = window.location.pathname;
    return path.includes('item') && path.includes('change');
}

function updateEditHref(anchor, fieldName){
    if (anchor) {
        key = document.querySelector('#id_key').value;
        const baseUrl = anchor.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(key + "_" + fieldName)}`;
        anchor.setAttribute('href', newHref);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const titleAddButton = document.querySelector('#add_id_title');
    const briefAddButton = document.querySelector('#add_id_brief');
    const nameAddButton = document.querySelector('#add_id_name');
    const descriptionAddButton = document.querySelector('#add_id_description');
    const rarityAddButton = document.querySelector('#add_id_rarity');
    const raritySelect = document.querySelector('#id_rarity');
    const itemTypeSelect = document.querySelector('#id_type');

    const identifierInput = document.querySelector('#id_identifier');

    const editNameButton = document.querySelector('#change_id_name');
    const editDescriptionButton = document.querySelector('#change_id_description');

    function elementsToUpdate() {
        updateHref(titleAddButton, 'title');
        updateHref(briefAddButton, 'brief');
        updateHref(nameAddButton, 'name');
        updateHref(descriptionAddButton, 'description');
        updateHref(rarityAddButton, 'rarity');

        if (isEditingForm()) {
            updateEditHref(editNameButton, 'name');
            updateEditHref(editDescriptionButton, 'description');
        }
    }

    if(identifierInput){
        identifierInput.addEventListener('input', elementsToUpdate);
    }

    if (raritySelect) {
        raritySelect.addEventListener('input', elementsToUpdate);
    }

    if (itemTypeSelect) {
        itemTypeSelect.addEventListener('input', elementsToUpdate);
    }

    if (isEditingForm()) {            
        if(editNameButton) {
            editNameButton.addEventListener('input', elementsToUpdate);
        }

        if(editDescriptionButton) {
            editDescriptionButton.addEventListener('input', elementsToUpdate);
        }
    }

    isEditingLocalizationPopup = 
        window.location.href.includes('popup') &&
        window.location.href.includes('change') &&
        window.location.href.includes('localization');
    
    if(isEditingLocalizationPopup) {
        const identifierURLParam = new URL(window.location.href).searchParams.get('identifier');

        if(identifierURLParam != identifierInput.value){
            identifierInput.value = identifierURLParam;
            identifierInput.dispatchEvent(new Event("input", { bubbles: true }));   
        }
    }
});