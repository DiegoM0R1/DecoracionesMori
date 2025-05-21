/**
 * Script principal para la web DecoracionesMori
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Scripts principales cargados correctamente');
    
    // Manejo del menú móvil
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            // Añadir clase para animar el botón
            this.classList.toggle('active');
        });
    }
    
    // Animación al hacer scroll
    function animateOnScroll() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 50) {
                element.classList.add('visible');
            }
        });
    }
    
    // Iniciar animaciones al cargar
    animateOnScroll();
    
    // Ejecutar animaciones al hacer scroll
    window.addEventListener('scroll', animateOnScroll);
    
    // Cerrar automáticamente las alertas después de 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
});