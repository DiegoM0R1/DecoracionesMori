document.addEventListener('DOMContentLoaded', function () {
  // Añadir clase 'reveal' a los elementos que queremos animar
  const elementsToReveal = document.querySelectorAll(
    '.section-title, .section-subtitle, .service-card, .feature-box, .testimonial-item'
  );

  elementsToReveal.forEach(function (element) {
    element.classList.add('reveal');
  });

  // Función para verificar si un elemento está en la vista
  function checkIfInView() {
    const windowHeight = window.innerHeight;
    const windowTopPosition = window.pageYOffset;
    const windowBottomPosition = windowTopPosition + windowHeight;

    elementsToReveal.forEach(function (element) {
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

  // Verificar al cargar la página
  checkIfInView();

  // Verificar al hacer scroll
  window.addEventListener('scroll', checkIfInView);

  // Mejorar la transición entre slides del carrusel
  const heroCarousel = document.querySelector('.hero-carousel');
  if (heroCarousel) {
    heroCarousel.addEventListener('slide.bs.carousel', function (e) {
      const activeItem = this.querySelector('.active');
      const activeCaption = activeItem.querySelector('.carousel-caption');

      // Reset animations
      activeCaption.querySelector('h1').style.animation = 'none';
      activeCaption.querySelector('p').style.animation = 'none';
      activeCaption.querySelector('.btn').style.animation = 'none';

      setTimeout(function () {
        activeCaption.querySelector('h1').style.animation = '';
        activeCaption.querySelector('p').style.animation = '';
        activeCaption.querySelector('.btn').style.animation = '';
      }, 10);
    });
  }
});