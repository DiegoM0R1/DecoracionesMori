// Archivo: static/js/invoice-form.js

document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad para productos
    const productSelect = document.querySelector('select[name$="product"]');
    if (productSelect) {
        productSelect.addEventListener('change', function() {
            if (this.value) {
                // Obtener los datos del producto seleccionado
                fetch(`/admin/api/products/${this.value}/`)
                    .then(response => response.json())
                    .then(data => {
                        // Buscar el campo de precio en la misma fila
                        const row = this.closest('tr');
                        const priceInput = row.querySelector('input[name$="unit_price"]');
                        if (priceInput) {
                            priceInput.value = data.price_per_unit;
                        }
                    })
                    .catch(error => console.error('Error:', error));
            }
        });
    }
    
    // Funcionalidad similar para servicios
    const serviceSelect = document.querySelector('select[name$="service"]');
    if (serviceSelect) {
        serviceSelect.addEventListener('change', function() {
            if (this.value) {
                fetch(`/admin/api/services/${this.value}/`)
                    .then(response => response.json())
                    .then(data => {
                        const row = this.closest('tr');
                        const priceInput = row.querySelector('input[name$="unit_price"]');
                        if (priceInput) {
                            priceInput.value = data.base_price;
                        }
                    })
                    .catch(error => console.error('Error:', error));
            }
        });
    }
});