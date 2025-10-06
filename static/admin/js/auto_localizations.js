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
    const addButtonNames = [
        'title',
        'brief',
        'name',
        'description',
        'rarity',
        'message',
        'slogan',
        'button_text',
        'text',
    ];

    const addButtonsList = [];
    
    addButtonNames.forEach(buttonName => {
        addButtonsList.push({
            'name': buttonName,
            'anchor': document.querySelector(`#add_id_${buttonName}`)
        });
    });

    const raritySelect = document.querySelector('#id_rarity');
    const itemTypeSelect = document.querySelector('#id_type');

    const identifierInput = document.querySelector('#id_identifier');

    const editNameButton = document.querySelector('#change_id_name');
    const editDescriptionButton = document.querySelector('#change_id_description');

    function elementsToUpdate() {
        addButtonsList.forEach(button => {
            updateHref(button.anchor, button.name);
        });

        // if (isEditingForm()) {
        //     updateEditHref(editNameButton, 'name');
        //     updateEditHref(editDescriptionButton, 'description');
        // }
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

    document.addEventListener("generatedNewSanitizedKey", elementsToUpdate);

    if (isEditingForm()) {            
        if(editNameButton) {
            editNameButton.addEventListener('input', elementsToUpdate);
        }

        if(editDescriptionButton) {
            editDescriptionButton.addEventListener('input', elementsToUpdate);
        }
    }

    elementsToUpdate();

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