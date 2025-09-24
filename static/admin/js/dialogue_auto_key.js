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

    const npc = npcSelect.options[npcSelect.selectedIndex].text.split("npc_")[1];

    const typeValue = isEditingForm() ? typeSelect.innerText : typeSelect.value;
    keyInput.value = prefix + typeValue.toLowerCase() + "_" + npc + "_" + slug;

}

function updateAddRelatedLink(addRelatedLink, keyValue, suffix) {
    if(!addRelatedLink) return;
    
    // Update popup link
    const baseUrl = addRelatedLink.getAttribute('href').split('?')[0];
    const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(keyValue + suffix)}`;
    addRelatedLink.setAttribute('href', newHref);
}

document.addEventListener('DOMContentLoaded', function () {
    const identifierInput = document.querySelector('#id_identifier');
    const keyInput = document.querySelector('#id_key');
    const typeSelect = isEditingForm() ? document.querySelector('.field-type .readonly') : document.querySelector('#id_type');
    const npcSelect = document.querySelector('#id_npc');

    const updateRelatedLinks = () => {
            const addRelatedLinkquestPromptText = document.querySelector('#add_id_quest_prompt_dialogue-0-text');
            const addRelatedLinkquestPromptDenyText = document.querySelector('#add_id_quest_prompt_dialogue-0-deny_text');
            const addRelatedLinkquestPromptAcceptText = document.querySelector('#add_id_quest_prompt_dialogue-0-acccept_text');

            const addRelatedLinkBasicSequence = document.querySelector('#add_id_basic_dialogue-0-sequence');
            const addRelatedLinkQuestEndSequence = document.querySelector('#add_id_quest_end_dialogue-0-sequence');

            updateAddRelatedLink(addRelatedLinkquestPromptText, keyInput.value, "_single_item");
            updateAddRelatedLink(addRelatedLinkquestPromptDenyText, keyInput.value, "_deny_single_item");
            updateAddRelatedLink(addRelatedLinkquestPromptAcceptText, keyInput.value, "_accept_single_item");
            updateAddRelatedLink(addRelatedLinkBasicSequence, keyInput.value, "_basic_sequence");
            updateAddRelatedLink(addRelatedLinkQuestEndSequence, keyInput.value, "_quest_end_sequence");
    }

    const updateReferences = () => {
            updateKey(identifierInput, keyInput, npcSelect, typeSelect);
            updateRelatedLinks();
    };

    if (identifierInput && keyInput && npcSelect && typeSelect) {
        updateReferences();
        
        typeSelect.addEventListener('input', function () {
            updateReferences();
        });

        npcSelect.addEventListener('input', function () {
            updateReferences();
        });

        identifierInput.addEventListener('input', function () {
            updateReferences();
        });
    }

    document.addEventListener("dialogueSubtypeChange", function(e) {
        updateRelatedLinks();
    });
});