// Validación del formulario
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Integración con animaciones
    const elementsToAnimate = document.querySelectorAll(
        '.section-title, .section-subtitle, .contact-info, .card, .form-floating'
    );

    elementsToAnimate.forEach(function(element) {
        element.classList.add('reveal');
    });

    // Función para verificar si un elemento está en la vista
    function checkIfInView() {
        const windowHeight = window.innerHeight;
        const windowTopPosition = window.pageYOffset;
        const windowBottomPosition = windowTopPosition + windowHeight;

        elementsToAnimate.forEach(function(element) {
            const elementHeight = element.offsetHeight;
            const elementTopPosition =
                element.getBoundingClientRect().top + window.pageYOffset;
            const elementBottomPosition = elementTopPosition + elementHeight;

            // Verificar si el elemento está en la vista
            if (
                elementBottomPosition >= windowTopPosition &&
                elementTopPosition <= windowBottomPosition
            ) {
                element.classList.add('active');
            }
        });
    }

    // Verificar al cargar la página y al hacer scroll
    checkIfInView();
    window.addEventListener('scroll', checkIfInView);
    
    // Fetch all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Manejo del envío del formulario con AJAX (opcional)
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            // Solo si el formulario es válido
            if (contactForm.checkValidity()) {
                event.preventDefault();
                
                const formData = new FormData(contactForm);
                
                // Mostrar indicador de carga
                const submitBtn = contactForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';
                submitBtn.disabled = true;
                
                fetch(contactForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    // Mostrar mensaje de éxito/error
                    const formResult = document.getElementById('formResult');
                    if (data.success) {
                        formResult.innerHTML = `
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle me-2"></i> ${data.message}
                            </div>
                        `;
                        contactForm.reset();
                        contactForm.classList.remove('was-validated');
                    } else {
                        formResult.innerHTML = `
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-circle me-2"></i> ${data.message}
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    const formResult = document.getElementById('formResult');
                    formResult.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-2"></i> Ha ocurrido un error al enviar el mensaje. Por favor, inténtalo de nuevo.
                        </div>
                    `;
                })
                .finally(() => {
                    // Restaurar botón
                    submitBtn.innerHTML = originalBtnText;
                    submitBtn.disabled = false;
                });
            }
        });
    }
});

// Inicialización del mapa de Google
function initMap() {
    // Coordenadas de la empresa (reemplazar con las correctas)
    const companyLocation = { lat: -11.951673, lng: -76.977654 };
    
    const map = new google.maps.Map(document.getElementById("map") || document.querySelector('#vermapa iframe'), {
        zoom: 15,
        center: companyLocation,
        styles: [
            // Estilos personalizados del mapa (opcional)
            {
                "featureType": "administrative",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#444444"}]
            },
            {
                "featureType": "landscape",
                "elementType": "all",
                "stylers": [{"color": "#f2f2f2"}]
            },
            {
                "featureType": "poi",
                "elementType": "all",
                "stylers": [{"visibility": "off"}]
            },
            {
                "featureType": "road",
                "elementType": "all",
                "stylers": [{"saturation": -100},{"lightness": 45}]
            },
            {
                "featureType": "road.highway",
                "elementType": "all",
                "stylers": [{"visibility": "simplified"}]
            },
            {
                "featureType": "road.arterial",
                "elementType": "labels.icon",
                "stylers": [{"visibility": "off"}]
            },
            {
                "featureType": "transit",
                "elementType": "all",
                "stylers": [{"visibility": "off"}]
            },
            {
                "featureType": "water",
                "elementType": "all",
                "stylers": [{"color": "#4299e1"},{"visibility": "on"}]
            }
        ]
    });
    
    const marker = new google.maps.Marker({
        position: companyLocation,
        map: map,
        title: "Decoraciones Mori",
        animation: google.maps.Animation.DROP
    });
    
    // Contenido de la ventana de información
    const contentString = `
        <div style="padding: 10px; max-width: 200px;">
            <h5 style="margin: 0 0 5px; font-weight: bold; color: #4A5568;">Decoraciones Mori</h5>
            <p style="margin: 0 0 5px; font-size: 14px; color: #718096;">
                Urb. Mariscal Cáceres Mz P6 Lt 23, San Juan Lurigancho, Lima
            </p>
            <a href="tel:+51923614593" style="color: #3182CE; font-size: 13px; text-decoration: none;">
                +51 923 614 593
            </a>
        </div>
    `;
    
    const infoWindow = new google.maps.InfoWindow({
        content: contentString
    });
    
    marker.addListener("click", () => {
        infoWindow.open(map, marker);
    });
    
    // Abrir infoWindow por defecto
    infoWindow.open(map, marker);
}

// Detectar cuándo el elemento de mapa es visible y cargar el mapa
document.addEventListener('DOMContentLoaded', function() {
    const mapObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && typeof google !== 'undefined') {
                initMap();
                mapObserver.disconnect();
            }
        });
    });
    
    const mapElement = document.getElementById('vermapa');
    if (mapElement) {
        mapObserver.observe(mapElement);
    }
});