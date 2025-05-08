// animations.js - Versión avanzada para DecoracionesMori

document.addEventListener('DOMContentLoaded', function() {
    // Configuración de efectos AOS (Animate on Scroll)
    // Si decides incluir la biblioteca AOS, descomenta estas líneas
    /*
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true,
        mirror: false
    });
    */
    // Agregar al inicio del DOMContentLoaded
setTimeout(() => {
    document.querySelectorAll('.service-card').forEach(card => {
        card.style.opacity = '1';
        card.style.transform = 'none';
    });
}, 2000); // Failsafe después de 2 segundos
    // Animación para la aparición de elementos al hacer scroll (versión nativa)
    const fadeElems = document.querySelectorAll('.fade-in');
    
    // Función para verificar si un elemento es visible en la ventana
    const isElementInViewport = function(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.85
        );
    };
    
    // Función para mostrar elementos cuando son visibles
    const checkFade = function() {
        fadeElems.forEach(function(element) {
            if (isElementInViewport(element) && !element.classList.contains('appear')) {
                element.classList.add('appear');
            }
        });
    };
    
    // Ejecutar al cargar y al hacer scroll
    window.addEventListener('scroll', checkFade);
    window.addEventListener('resize', checkFade);
    
    // Llamar inmediatamente para animar elementos ya visibles
    setTimeout(checkFade, 100);
    
    // Asignar delays escalonados a elementos para crear efecto cascada
    const staggerItems = function(items, baseDelay = 0.1) {
        items.forEach(function(item, index) {
            // Asegurarse de que el elemento sea visible inicialmente
            item.style.opacity = '1';
            
            // Agregar las clases de animación después de un pequeño delay
            setTimeout(() => {
                item.style.transitionDelay = (index * baseDelay) + 's';
                item.classList.add('fade-in');
                // Forzar un reflow
                item.offsetHeight;
                // Agregar la clase appear inmediatamente después
                item.classList.add('appear');
            }, 100);
        });
    };
    
    // Animar elementos específicos con retrasos escalonados
    const serviceCards = document.querySelectorAll('.service-card');
if (serviceCards.length > 0) {
    staggerItems(serviceCards, 0.1);
}
    
    const categoryButtons = document.querySelectorAll('.category-filters .btn');
    staggerItems(categoryButtons, 0.05);
    
    const galleryImages = document.querySelectorAll('.service-gallery .service-detail-image');
    staggerItems(galleryImages, 0.1);
    
    const videoItems = document.querySelectorAll('.service-videos .service-detail-video');
    staggerItems(videoItems, 0.15);
    
    // Animaciones para tarjetas en hover
    const addHoverEffects = function() {
        // Efecto de hover para tarjetas de servicio
        const cards = document.querySelectorAll('.service-card');
        cards.forEach(function(card) {
            card.addEventListener('mouseenter', function() {
                this.querySelector('.card-img-top-container img')?.classList.add('hovered');
                this.querySelector('.btn')?.classList.add('btn-hover');
            });
            
            card.addEventListener('mouseleave', function() {
                this.querySelector('.card-img-top-container img')?.classList.remove('hovered');
                this.querySelector('.btn')?.classList.remove('btn-hover');
            });
        });
        
        // Efecto para tarjetas de categoría
        const categoryCards = document.querySelectorAll('.category-card');
        categoryCards.forEach(function(card) {
            card.addEventListener('mouseenter', function() {
                this.querySelector('img')?.classList.add('hovered');
                this.querySelector('.category-overlay')?.classList.add('hovered');
            });
            
            card.addEventListener('mouseleave', function() {
                this.querySelector('img')?.classList.remove('hovered');
                this.querySelector('.category-overlay')?.classList.remove('hovered');
            });
        });
    };
    
    addHoverEffects();
    
    // Contador de estadísticas animado
    const animateCounters = function() {
        const counters = document.querySelectorAll('.counter');
        
        counters.forEach(function(counter) {
            const target = parseInt(counter.getAttribute('data-target'));
            const duration = 2000; // ms
            const increment = target / (duration / 16); // 60fps
            let current = 0;
            
            const updateCounter = function() {
                current += increment;
                if (current < target) {
                    counter.textContent = Math.round(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target;
                }
            };
            
            // Detectar cuando el contador es visible
            const observer = new IntersectionObserver(function(entries) {
                if (entries[0].isIntersecting) {
                    requestAnimationFrame(updateCounter);
                    observer.disconnect();
                }
            }, { threshold: 0.5 });
            
            observer.observe(counter);
        });
    };
    
    animateCounters();
    
    // Efecto parallax para header de servicios
    const parallaxHeader = function() {
        const header = document.querySelector('.services-header');
        if (header) {
            window.addEventListener('scroll', function() {
                const scrolled = window.pageYOffset;
                header.style.backgroundPositionY = (scrolled * 0.4) + 'px';
            });
        }
    };
    
    parallaxHeader();
    
    // Animación para el hero de la página de inicio
    const animateHero = function() {
        const hero = document.querySelector('.home-hero');
        if (hero) {
            const title = hero.querySelector('h1');
            const subtitle = hero.querySelector('p');
            const button = hero.querySelector('.btn');
            
            if (title) title.classList.add('animated');
            
            if (subtitle) {
                setTimeout(function() {
                    subtitle.classList.add('animated');
                }, 400);
            }
            
            if (button) {
                setTimeout(function() {
                    button.classList.add('animated');
                }, 800);
            }
        }
    };
    
    animateHero();
    
    // Toggle para modo oscuro
    const setupDarkMode = function() {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            // Verificar preferencia guardada
            if (localStorage.getItem('darkMode') === 'enabled') {
                document.body.classList.add('dark-mode');
                darkModeToggle.checked = true;
            }
            
            darkModeToggle.addEventListener('change', function() {
                if (this.checked) {
                    document.body.classList.add('dark-mode');
                    localStorage.setItem('darkMode', 'enabled');
                } else {
                    document.body.classList.remove('dark-mode');
                    localStorage.setItem('darkMode', 'disabled');
                }
            });
        }
    };
    
    setupDarkMode();
    
    // Animación para el menú móvil
    const setupMobileMenu = function() {
        const mobileMenuButton = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (mobileMenuButton && navbarCollapse) {
            mobileMenuButton.addEventListener('click', function() {
                if (navbarCollapse.classList.contains('show')) {
                    // Cerrando menú
                    navbarCollapse.style.height = navbarCollapse.offsetHeight + 'px';
                    setTimeout(() => {
                        navbarCollapse.style.height = '0px';
                    }, 10);
                } else {
                    // Abriendo menú
                    navbarCollapse.style.height = 'auto';
                    const height = navbarCollapse.offsetHeight;
                    navbarCollapse.style.height = '0px';
                    setTimeout(() => {
                        navbarCollapse.style.height = height + 'px';
                    }, 10);
                }
            });
            
            // Ajustar después de la transición
            navbarCollapse.addEventListener('transitionend', function() {
                if (navbarCollapse.classList.contains('show')) {
                    navbarCollapse.style.height = 'auto';
                }
            });
        }
    };
    
    setupMobileMenu();
    
    // Efecto de scroll suave para anclas
    const setupSmoothScroll = function() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                if (this.getAttribute('href') !== '#') {
                    e.preventDefault();
                    
                    const targetId = this.getAttribute('href');
                    const targetElement = document.querySelector(targetId);
                    
                    if (targetElement) {
                        window.scrollTo({
                            top: targetElement.offsetTop - 80, // Ajuste para el navbar fijo
                            behavior: 'smooth'
                        });
                    }
                }
            });
        });
    };
    
    setupSmoothScroll();
    
    // Efecto para hacer el navbar transparente al inicio y sólido al hacer scroll
    const setupNavbarScroll = function() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            // Inicialmente transparente si estamos en el top
            if (window.scrollY === 0 && !navbar.classList.contains('navbar-absolute')) {
                navbar.classList.add('navbar-transparent');
            }
            
            window.addEventListener('scroll', function() {
                if (window.scrollY > 50) {
                    navbar.classList.remove('navbar-transparent');
                    navbar.classList.add('navbar-scrolled');
                } else {
                    navbar.classList.add('navbar-transparent');
                    navbar.classList.remove('navbar-scrolled');
                }
            });
        }
    };
    
    setupNavbarScroll();
    
    // Inicializar carruseles si existen (requiere Bootstrap)
    const initCarousels = function() {
        const carousels = document.querySelectorAll('.carousel');
        if (carousels.length > 0 && typeof bootstrap !== 'undefined') {
            carousels.forEach(function(carousel) {
                new bootstrap.Carousel(carousel, {
                    interval: 5000,
                    touch: true
                });
            });
        }
    };
    
    initCarousels();
    
    // Filtro con efecto fade para galería (opcional)
    const setupGalleryFilter = function() {
        const filterButtons = document.querySelectorAll('.gallery-filter-btn');
        const galleryItems = document.querySelectorAll('.gallery-item');
        
        if (filterButtons.length > 0 && galleryItems.length > 0) {
            filterButtons.forEach(function(button) {
                button.addEventListener('click', function() {
                    // Actualizar botones activos
                    filterButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    const filterValue = this.getAttribute('data-filter');
                    
                    // Filtrar elementos
                    galleryItems.forEach(function(item) {
                        item.style.opacity = '0';
                        item.style.transform = 'scale(0.8)';
                        
                        setTimeout(function() {
                            if (filterValue === 'all' || item.classList.contains(filterValue)) {
                                item.style.display = 'block';
                                setTimeout(function() {
                                    item.style.opacity = '1';
                                    item.style.transform = 'scale(1)';
                                }, 50);
                            } else {
                                item.style.display = 'none';
                            }
                        }, 300);
                    });
                });
            });
        }
    };
    
    setupGalleryFilter();
    
    // Inicializar Lightbox para galería de imágenes (si decides usar una librería de lightbox)
    const initLightbox = function() {
        // Si decides incluir una biblioteca de lightbox (como SimpleLightbox, GLightbox, etc.)
        // Aquí puedes inicializarla
        
        // Ejemplo para SimpleLightbox:
        /*
        if (typeof SimpleLightbox !== 'undefined') {
            new SimpleLightbox('.gallery a', {
                nav: true,
                captions: true,
                captionsData: 'alt',
                captionDelay: 250
            });
        }
        */
    };
    
    initLightbox();
    
    // Efectos visuales adicionales para elementos específicos
    const addSpecialEffects = function() {
        // Efecto de revelar texto letra por letra (opcional)
        const textRevealElements = document.querySelectorAll('.text-reveal');
        textRevealElements.forEach(function(element) {
            const text = element.textContent;
            element.textContent = '';
            
            // Crear contenedor para letras
            const wrapper = document.createElement('span');
            wrapper.className = 'text-reveal-wrapper';
            
            // Crear span para cada letra
            for (let i = 0; i < text.length; i++) {
                const letterSpan = document.createElement('span');
                letterSpan.className = 'text-reveal-letter';
                letterSpan.style.transitionDelay = (i * 0.03) + 's';
                letterSpan.textContent = text[i] === ' ' ? '\u00A0' : text[i];
                wrapper.appendChild(letterSpan);
            }
            
            element.appendChild(wrapper);
            
            // Animar cuando sea visible
            const observer = new IntersectionObserver(function(entries) {
                if (entries[0].isIntersecting) {
                    const letters = element.querySelectorAll('.text-reveal-letter');
                    letters.forEach(letter => letter.classList.add('revealed'));
                    observer.disconnect();
                }
            });
            
            observer.observe(element);
        });
    };
    
    addSpecialEffects();
    
    // Inicializar tooltips y popovers (requiere Bootstrap)
    const initTooltips = function() {
        if (typeof bootstrap !== 'undefined') {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
            
            var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function(popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        }
    };
    
    initTooltips();
});