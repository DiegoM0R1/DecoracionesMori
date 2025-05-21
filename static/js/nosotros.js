/* Estilos para la sección "Quiénes Somos" */
    document.addEventListener('DOMContentLoaded', function() {
        // Añadir clases para animaciones de aparición en scroll
        const elementsToFadeIn = document.querySelectorAll('.section-title, .section-subtitle, .cta-section');
        const elementsToFadeInLeft = document.querySelectorAll('.position-relative, .mission-card');
        const elementsToFadeInRight = document.querySelectorAll('.col-lg-6:nth-child(even)');
        const elementsToZoomIn = document.querySelectorAll('.team-card, .stat-card');
        
        // Añadir clases de animación
        elementsToFadeIn.forEach(element => element.classList.add('fade-in'));
        elementsToFadeInLeft.forEach(element => element.classList.add('fade-in-left'));
        elementsToFadeInRight.forEach(element => element.classList.add('fade-in-right'));
        elementsToZoomIn.forEach(element => element.classList.add('zoom-in'));
        
        // Función para detectar elementos en la vista
        function checkIfInView() {
            const windowHeight = window.innerHeight;
            const windowTopPosition = window.pageYOffset;
            const windowBottomPosition = windowTopPosition + windowHeight - 100;
            
            // Comprobar todos los elementos con animaciones
            document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .zoom-in').forEach(function(element) {
                const elementHeight = element.offsetHeight;
                const elementTopPosition = element.getBoundingClientRect().top + window.pageYOffset;
                const elementBottomPosition = elementTopPosition + elementHeight;
                
                // Verificar si el elemento está en la vista
                if ((elementBottomPosition >= windowTopPosition) && (elementTopPosition <= windowBottomPosition)) {
                    element.classList.add('active');
                }
            });
        }
        
        // Comprobar elementos al cargar la página
        window.addEventListener('load', checkIfInView);
        
        // Comprobar elementos al hacer scroll
        window.addEventListener('scroll', checkIfInView);
    
        // Contador animado para las estadísticas
        function animateCounter(element, target) {
            let current = 0;
            const increment = target > 1000 ? 25 : 1;
            const duration = 2000;
            const steps = Math.ceil(duration / (1000 / 60));
            const step = Math.floor(target / steps);
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    element.textContent = target + '+';
                    clearInterval(timer);
                } else {
                    element.textContent = current + '+';
                }
            }, duration / steps);
        }
    
        // Observer para iniciar los contadores cuando sean visibles
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;
                    const value = parseInt(target.textContent);
                    animateCounter(target, value);
                    counterObserver.unobserve(target);
                }
            });
        }, { threshold: 0.5 });
    
        // Observar los elementos de contador
        document.querySelectorAll('.stat-card h3').forEach(counter => {
            counterObserver.observe(counter);
        });
    });