function updateFields(identifierInput, keyInput) {
    const prefix = identifierInput.dataset.keyPrefix || '';
    const slug = identifierInput.value
        .toLowerCase()
        .replace(/[^\w\s]/g, '')    // elimina caracteres no alfanuméricos
        .trim()
        .replace(/\s+/g, '_');      // reemplaza espacios por guiones bajos

    keyInput.value = prefix + slug;
}

document.addEventListener('DOMContentLoaded', function () {
    const identifierInput = document.querySelector('#id_identifier');
    const keyInput = document.querySelector('#id_key');

    const isItemView = document.querySelector('body').classList.contains('model-item');

    if (identifierInput && keyInput && !isItemView) {
        updateFields(identifierInput, keyInput);
        identifierInput.addEventListener('input', function () {
            updateFields(identifierInput, keyInput);
        });
    }
});