(function($) {
    $(document).ready(function() {
        // Función para autocompletar el precio cuando se selecciona un producto
        function setupProductPriceAutocomplete() {
            // Para productos - Usando selector estándar de Django admin
            $('select[name$="-product"]').on('change', function() {
                var productId = $(this).val();
                if (productId) {
                    // Obtener la fila (tr) actual
                    var row = $(this).closest('tr');
                    // Construir URL para el API
                    var url = '/api/products/' + productId + '/';
                    
                    // Llamada AJAX para obtener datos del producto
                    $.get(url, function(data) {
                        // Encontrar el campo de precio unitario en la misma fila
                        var priceField = row.find('input[name$="-unit_price"]');
                        if (priceField.length) {
                            priceField.val(data.price_per_unit);
                            // Disparar evento change para activar cualquier cálculo relacionado
                            priceField.trigger('change');
                        }
                    });
                }
            });
            
            // Similar para servicios
            $('select[name$="-service"]').on('change', function() {
                var serviceId = $(this).val();
                if (serviceId) {
                    var row = $(this).closest('tr');
                    var url = '/api/services/' + serviceId + '/';
                    
                    $.get(url, function(data) {
                        var priceField = row.find('input[name$="-unit_price"]');
                        if (priceField.length) {
                            priceField.val(data.base_price);
                            priceField.trigger('change');
                        }
                    });
                }
            });
        }
        
        // Inicializar el autocompletado
        setupProductPriceAutocomplete();
        
        // Para manejar formularios inline dinámicos que se añaden
        $(document).on('formset:added', function(event, $row, formsetName) {
            setupProductPriceAutocomplete();
        });
    });
})(django.jQuery);