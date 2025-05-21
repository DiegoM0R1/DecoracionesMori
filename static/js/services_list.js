/**
 * Script para la página de lista de servicios
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Script de servicios cargado correctamente');
    
    // Filtrado de servicios por categoría
    const filterButtons = document.querySelectorAll('.filter-btn');
    const serviceItems = document.querySelectorAll('.service-item');
    
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remover clase activa de todos los botones
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Añadir clase activa al botón clickeado
                this.classList.add('active');
                
                // Obtener categoría seleccionada
                const filterValue = this.getAttribute('data-filter');
                
                // Filtrar servicios
                serviceItems.forEach(item => {
                    if (filterValue === 'all') {
                        item.style.display = 'block';
                        setTimeout(() => {
                            item.classList.add('show');
                        }, 50);
                    } else {
                        if (item.classList.contains(filterValue)) {
                            item.style.display = 'block';
                            setTimeout(() => {
                                item.classList.add('show');
                            }, 50);
                        } else {
                            item.classList.remove('show');
                            setTimeout(() => {
                                item.style.display = 'none';
                            }, 300);
                        }
                    }
                });
            });
        });
    }
    
    // Animación al cargar la página
    serviceItems.forEach((item, index) => {
        setTimeout(() => {
            item.classList.add('show');
        }, 100 * index);
    });
});