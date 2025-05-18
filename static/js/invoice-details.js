document.addEventListener('DOMContentLoaded', function() {
    // Función principal para autocompletar precios
    function setupProductPriceAutocomplete() {
        // Obtener todos los selectores de productos (pueden ser múltiples filas)
        const productSelects = document.querySelectorAll('select[name*="product"]');
        const serviceSelects = document.querySelectorAll('select[name*="service"]');
        
        // Configurar eventos para productos
        productSelects.forEach(select => {
            select.addEventListener('change', function() {
                if (this.value) {
                    fetch(`/api/products/${this.value}/`)
                        .then(response => response.json())
                        .then(data => {
                            // Encontrar el campo de precio en la misma fila
                            const row = this.closest('tr');
                            if (!row) return;
                            
                            const priceInput = row.querySelector('input[name*="unit_price"]');
                            if (priceInput) {
                                priceInput.value = data.price_per_unit;
                                // Actualizar subtotal si es posible
                                updateSubtotal(row);
                            }
                        });
                }
            });
        });
        
        // Configurar eventos para servicios
        serviceSelects.forEach(select => {
            select.addEventListener('change', function() {
                if (this.value) {
                    fetch(`/api/services/${this.value}/`)
                        .then(response => response.json())
                        .then(data => {
                            const row = this.closest('tr');
                            if (!row) return;
                            
                            const priceInput = row.querySelector('input[name*="unit_price"]');
                            if (priceInput) {
                                priceInput.value = data.base_price;
                                updateSubtotal(row);
                            }
                        });
                }
            });
        });
        
        // También configurar para cambios en cantidad
        const quantityInputs = document.querySelectorAll('input[name*="quantity"]');
        quantityInputs.forEach(input => {
            input.addEventListener('change', function() {
                const row = this.closest('tr');
                if (row) updateSubtotal(row);
            });
        });
    }
    
    // Función para actualizar subtotal
    function updateSubtotal(row) {
        const quantityInput = row.querySelector('input[name*="quantity"]');
        const priceInput = row.querySelector('input[name*="unit_price"]');
        const discountInput = row.querySelector('input[name*="discount"]');
        const subtotalDisplay = row.querySelector('.subtotal-display'); // Ajusta según tu HTML
        
        if (quantityInput && priceInput && subtotalDisplay) {
            const quantity = parseFloat(quantityInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const discount = discountInput ? (parseFloat(discountInput.value) || 0) : 0;
            
            const subtotal = (quantity * price) - discount;
            subtotalDisplay.textContent = subtotal.toFixed(2);
            
            // Si tienes un campo oculto para subtotal
            const subtotalInput = row.querySelector('input[name*="subtotal"]');
            if (subtotalInput) subtotalInput.value = subtotal.toFixed(2);
        }
    }
    
    // Inicializar la funcionalidad
    setupProductPriceAutocomplete();
    
    // Para manejar filas añadidas dinámicamente
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                setupProductPriceAutocomplete();
            }
        });
    });
    
    // Observar cambios en la tabla o contenedor de items
    const itemsContainer = document.querySelector('.invoice-items-container') || document.body;
    observer.observe(itemsContainer, { childList: true, subtree: true });
});