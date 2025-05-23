# site_config/urls.py

from django.urls import path
from . import views # Importa tus vistas de la app site_config

app_name = 'site_config' # Es una buena práctica definir un namespace para la app

urlpatterns = [
    # Ejemplo: Si tuvieras una vista 'home' en site_config/views.py
    # path('', views.home_view, name='home'),
    # Si tienes la vista del carrusel y otras páginas principales en esta app:
    # path('', views.pagina_inicio, name='home'), # Asumiendo que 'pagina_inicio' es tu vista principal
    # path('nosotros/', views.nosotros_view, name='nosotros'),
    # path('contacto/', views.contacto_view, name='contacto'),
    # path('servicios/', views.servicios_view, name='service_list'),

    # Si no tienes vistas aquí aún, puedes dejar urlpatterns vacío por ahora,
    # pero asegúrate de que la variable urlpatterns exista:
    # urlpatterns = []
]