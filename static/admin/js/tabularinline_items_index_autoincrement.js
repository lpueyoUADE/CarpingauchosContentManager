document.addEventListener("DOMContentLoaded", function() {
    // Función auxiliar: cuando se añade un nuevo form inline
    document.body.addEventListener("formset:added", function(event) {

        let relatedSet = 'items';

        let newRow = event.target;  // el nuevo inline agregado
        let allRows = newRow.closest(".inline-group").querySelectorAll(`.dynamic-${relatedSet}`);  

        if (allRows.length > 1) {
            let prevRow = allRows[allRows.length - 2]; // penúltima fila
            let prevIndexInput = prevRow.querySelector("input[name$='index']");
            let newIndexInput = newRow.querySelector("input[name$='index']");

            if (prevIndexInput && newIndexInput) {
                let prevValue = parseInt(prevIndexInput.value) || 0;
                newIndexInput.value = prevValue + 1;
            }
        } else {
            // si es la primera fila, arranca en 1
            let newIndexInput = newRow.querySelector("input[name$='index']");
            if (newIndexInput) {
                newIndexInput.value = 1;
            }
        }
    });
});