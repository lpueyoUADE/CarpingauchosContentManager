function isEditingDialogueForm() {
    const path = window.location.pathname;
    return path.includes('dialogue') && path.includes('change');
}

function updateAddRelatedLink(addRelatedLink, model, keyValue, prefix, suffix) {
    if(!addRelatedLink) return;

    getSanitizedKey(keyValue, model, {
        "prefix": prefix,
        "slug": keyValue,
        "suffix": suffix
    }, (updatedKey) => {
        // Update popup link
        const baseUrl = addRelatedLink.getAttribute('href').split('?')[0];
        const newHref = `${baseUrl}?_popup=1&identifier=${encodeURIComponent(updatedKey)}`;
        addRelatedLink.setAttribute('href', newHref);
    }, false);
}

function updateKey(identifierInput, keyInput, npcSelect, typeSelect) {
    getSanitizedKey(keyInput, "Dialogue", {
        "prefix": identifierInput.dataset.keyPrefix,
        "type": isEditingDialogueForm() ? typeSelect.innerText : typeSelect.value,
        "npc": npcSelect.options[npcSelect.selectedIndex].text,
        "slug": identifierInput.value,
    }, () => {
        const addRelatedLinkquestPromptText = document.querySelector('#add_id_quest_prompt_dialogue-0-text');
        const addRelatedLinkquestPromptDenyText = document.querySelector('#add_id_quest_prompt_dialogue-0-deny_text');
        const addRelatedLinkquestPromptAcceptText = document.querySelector('#add_id_quest_prompt_dialogue-0-acccept_text');

        const addRelatedLinkBasicSequence = document.querySelector('#add_id_basic_dialogue-0-sequence');
        const addRelatedLinkQuestEndSequence = document.querySelector('#add_id_quest_end_dialogue-0-sequence');

        updateAddRelatedLink(addRelatedLinkquestPromptText, "DialogueSingleItem", keyInput.value, "dialoguesingleitem_", "single_item");
        updateAddRelatedLink(addRelatedLinkquestPromptDenyText, "DialogueSingleItem", keyInput.value, "dialoguesingleitem_", "deny_single_item");
        updateAddRelatedLink(addRelatedLinkquestPromptAcceptText, "DialogueSingleItem", keyInput.value, "dialoguesingleitem_", "accept_single_item");
        updateAddRelatedLink(addRelatedLinkBasicSequence, "DialogueSequence", keyInput.value, "dialoguesequence_", "");
        updateAddRelatedLink(addRelatedLinkQuestEndSequence, "DialogueSequence", keyInput.value, "dialoguesequence_", "");
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const identifierInput = document.querySelector('#id_identifier');
    const keyInput = document.querySelector('#id_key');
    const typeSelect = isEditingDialogueForm() ? document.querySelector('.field-type .readonly') : document.querySelector('#id_type');
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

    document.addEventListener("dialogueSubtypeChange", function(e) {
        updateKey(identifierInput, keyInput, npcSelect, typeSelect);
    });
});