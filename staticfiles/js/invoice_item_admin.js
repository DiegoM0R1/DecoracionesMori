// static/js/invoice_item_admin.js
document.addEventListener('DOMContentLoaded', function() {
    // Función para manejar la visibilidad de los campos según el tipo de ítem
    function handleItemTypeChange(row) {
        const itemTypeSelect = row.querySelector('select[name$="-item_type"]');
        const serviceField = row.querySelector('select[name$="-service"]').closest('.field-service');
        const productField = row.querySelector('select[name$="-product"]').closest('.field-product');
        
        if (itemTypeSelect) {
            // Ocultar o mostrar campos según el tipo seleccionado
            function updateFields() {
                const selectedValue = itemTypeSelect.value;
                
                if (selectedValue === 'service') {
                    serviceField.style.display = 'block';
                    productField.style.display = 'none';
                } else if (selectedValue === 'product') {
                    serviceField.style.display = 'none';
                    productField.style.display = 'block';
                } else {
                    // Para 'other'
                    serviceField.style.display = 'none';
                    productField.style.display = 'none';
                }
            }
            
            // Actualizar al cargar y cuando cambie el valor
            updateFields();
            itemTypeSelect.addEventListener('change', updateFields);
        }
    }
    
    // Manejar filas existentes
    document.querySelectorAll('.dynamic-invoiceitem_set').forEach(handleItemTypeChange);
    
    // Manejar nuevas filas cuando se añaden
    django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
        if (formsetName === 'invoiceitem_set') {
            handleItemTypeChange($row[0]);
        }
    });
    
    // Calcular totales cuando cambian los valores
    function updateSubtotal(row) {
        const quantity = parseFloat(row.querySelector('input[name$="-quantity"]').value) || 0;
        const unitPrice = parseFloat(row.querySelector('input[name$="-unit_price"]').value) || 0;
        const discount = parseFloat(row.querySelector('input[name$="-discount"]').value) || 0;
        
        const subtotal = (quantity * unitPrice) - discount;
        row.querySelector('input[name$="-subtotal"]').value = subtotal.toFixed(2);
    }
    
    // Añadir event listeners para recalcular
    document.querySelectorAll('.dynamic-invoiceitem_set').forEach(row => {
        row.querySelector('input[name$="-quantity"]').addEventListener('change', () => updateSubtotal(row));
        row.querySelector('input[name$="-unit_price"]').addEventListener('change', () => updateSubtotal(row));
        row.querySelector('input[name$="-discount"]').addEventListener('change', () => updateSubtotal(row));
    });
});

// static/js/invoice_appointment.js
document.addEventListener('DOMContentLoaded', function() {
    // Obtener los campos relevantes
    const advanceInput = document.querySelector('input[name="advance_payment"]');
    const appointmentField = document.querySelector('input[name="appointment"]');
    const statusSelect = document.querySelector('select[name="status"]');
    
    if (advanceInput && appointmentField && appointmentField.value) {
        advanceInput.addEventListener('change', function() {
            // Si el adelanto es de al menos 50 soles, mostrar mensaje
            if (parseFloat(this.value) >= 50) {
                // Alternativamente, podríamos cambiar automáticamente el estado
                // pero es mejor informar al usuario y dejar que tome la decisión
                const message = document.createElement('div');
                message.className = 'alert alert-info';
                message.innerHTML = 'Al guardar con un adelanto de 50 soles o más, ' +
                                    'la cita pasará automáticamente a estado "Confirmada".';
                
                // Insertar mensaje después del campo de adelanto
                this.parentNode.appendChild(message);
            }
        });
    }
});