function initGrids() {
    document.querySelectorAll('[data-widget-container]').forEach(container => {
        const selectedImg = container.querySelector('#selected-file');
        const selectedName = container.querySelector('#selected-name');
        const selectElement = container.querySelector('select');

        const selectedElement = container.querySelector('.grid-item.selected');

        const filterInput = container.querySelector('#grid-filter');

        if (selectedElement) {
            selectedImg.src = selectedElement.dataset.img;
            selectedName.textContent = selectedElement.dataset.name;
            selectedElement.classList.add('selected'); // marcarlo como seleccionado
            selectElement.value = selectedElement.dataset.value;
        }

        const items = container.querySelectorAll('.grid-item');

        // Click en cada file
        items.forEach(item => {
            item.addEventListener('click', function() {
                container.querySelectorAll('.grid-item').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
                selectElement.value = item.dataset.value;

                // Actualizar panel lateral
                selectedImg.src = item.dataset.img;
                selectedName.textContent = item.dataset.name;
            });
            // Filtro por nombre
            filterInput.addEventListener('input', function() {
                const query = this.value.toLowerCase();
                items.forEach(item => {
                    const label = item.dataset.name.toLowerCase();
                    item.style.display = label.includes(query) ? '' : 'none';
                });
            });
        });
    });
}

document.addEventListener("DOMContentLoaded", function() {
    document.addEventListener("itemSubtypeChange", function(e) {
        initGrids();
    });

    initGrids();
});