// Scripts.js - JavaScript principal del sitio

document.addEventListener('DOMContentLoaded', function() {
    
    // Inicializar carrusel con configuraciones personalizadas
    const carousel = document.querySelector('#heroCarousel');
    if (carousel) {
        const bsCarousel = new bootstrap.Carousel(carousel, {
            interval: 5000,
            wrap: true,
            pause: 'hover'
        });
        
        // Pausar carrusel cuando el usuario interactúa
        carousel.addEventListener('mouseenter', function() {
            bsCarousel.pause();
        });
        
        carousel.addEventListener('mouseleave', function() {
            bsCarousel.cycle();
        });
    }
    
    // Animaciones suaves para elementos que aparecen
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);
    
    // Observar elementos para animaciones
    document.querySelectorAll('.card, .section-title, .btn').forEach(el => {
        observer.observe(el);
    });
    
    // Smooth scroll para enlaces internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Efecto de typing para títulos principales
    function typeWriter(element, text, speed = 100) {
        let i = 0;
        element.innerHTML = '';
        
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        type();
    }
    
    // Aplicar efecto typing a títulos con clase 'typing-effect'
    document.querySelectorAll('.typing-effect').forEach(element => {
        const text = element.textContent;
        typeWriter(element, text, 80);
    });
    
    // Validación mejorada de formularios
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Mostrar/ocultar botón de "volver arriba"
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTopButton.className = 'btn btn-primary position-fixed';
    backToTopButton.style.cssText = `
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: none;
        opacity: 0;
        transition: all 0.3s ease;
    `;
    document.body.appendChild(backToTopButton);
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
            setTimeout(() => backToTopButton.style.opacity = '1', 10);
        } else {
            backToTopButton.style.opacity = '0';
            setTimeout(() => backToTopButton.style.display = 'none', 300);
        }
    });
    
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Debug: Verificar si las imágenes del carrusel están cargando
    const carouselImages = document.querySelectorAll('.carousel-item img');
    carouselImages.forEach((img, index) => {
        img.addEventListener('load', function() {
            console.log(`Imagen del carrusel ${index + 1} cargada correctamente`);
        });
        
        img.addEventListener('error', function() {
            console.error(`Error al cargar imagen del carrusel ${index + 1}: ${this.src}`);
        });
    });
    
    console.log('Scripts.js cargado correctamente');
});