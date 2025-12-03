# appointments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from .models import Appointment, ScheduledWorkDay, WorkScheduleTemplate # Importar nuevos modelos
from .forms import AppointmentRequestForm
# from accounts.models import User # Usar settings.AUTH_USER_MODEL
from django.conf import settings
from services.models import Service
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt # ¡Usar con cuidado! Mejor API con tokens
import requests
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy # Para success_url
from django.contrib import messages
import datetime
from django.utils.translation import gettext_lazy as _
User = settings.AUTH_USER_MODEL
from django.urls import reverse # O reverse_lazy si es necesario
from django.utils.translation import gettext # Importa gettext
# Al inicio de tu appointments/views.py
from django.contrib.auth import get_user_model
from .utils import send_appointment_received_email
# ... otras importaciones ...
User = get_user_model() # En lugar de User = settings.AUTH_USER_MODEL


class AppointmentRequestView(LoginRequiredMixin, CreateView):
    login_url = 'account_login' # Asegúrate que esta URL name exista en tu app accounts/urls.py
    model = Appointment
    form_class = AppointmentRequestForm
    template_name = 'appointments/request_appointment.html'
    # Redirigir a la página de éxito o al detalle de la cita creada
    # success_url = reverse_lazy('appointments:success') # O a detalle

    def get_success_url(self):
        # Redirigir al detalle de la cita recién creada
        return reverse_lazy('appointments:appointment_detail', kwargs={'appointment_id': self.object.pk})

    # En appointments/views.py, dentro de la clase AppointmentRequestView

    def get_form_kwargs(self):
        """Pasar service_id y user al formulario.""" # Descripción actualizada
        kwargs = super().get_form_kwargs()
        kwargs['service_id'] = self.kwargs.get('service_id')
        kwargs['user'] = self.request.user # <-- AÑADE ESTA LÍNEA
        return kwargs

    def get_context_data(self, **kwargs):
        """Añadir servicio al contexto."""
        context = super().get_context_data(**kwargs)
        context['service'] = get_object_or_404(Service, pk=self.kwargs.get('service_id'))

        context['MAPS_API_KEY'] = settings.MAPS_API_KEY 
        
        # Añadir traducciones para JavaScript
        context['js_translations'] = {
            'marker_title': gettext('Arrastra para ajustar la ubicación exacta'),
            'geocoding_failed': gettext('Geocodificación inversa falló:'),
            'autocomplete_no_geometry': gettext('Lugar de Autocomplete no tiene geometría:'),
            'alert_dni_error': gettext('Error al buscar DNI:'), # Ejemplo si tienes alertas en DNI JS
            'alert_config_error': gettext('Error de configuración interna. Por favor, recarga la página.'), # Ejemplo
            # Añade aquí cualquier otra cadena de texto que uses en alert() o console.warn()
            # que quieras que sea traducible.
        }
        return context

    def form_valid(self, form):
        """
        Procesa el formulario: actualiza el usuario (Cliente) según sea Empresa o Persona
        y asigna la cita.
        """
        user_to_update = self.request.user
        client_type = form.cleaned_data.get('client_type')

        # ---------------------------------------------------------
        # 1. LÓGICA PARA EMPRESA (RUC)
        # ---------------------------------------------------------
        if client_type == 'empresa':
            ruc = form.cleaned_data.get('ruc')
            razon_social = form.cleaned_data.get('razon_social')
            
            # Guardar RUC
            if hasattr(user_to_update, 'ruc'):
                user_to_update.ruc = ruc
            
            # Usamos el campo first_name para la Razón Social
            if razon_social:
                user_to_update.first_name = razon_social
                user_to_update.last_name = "" # Las empresas no tienen apellidos

        # ---------------------------------------------------------
        # 2. LÓGICA PARA PERSONA (DNI)
        # ---------------------------------------------------------
        else:
            dni = form.cleaned_data.get('dni', '').strip()
            
            # Guardar DNI
            if hasattr(user_to_update, 'dni'):
                user_to_update.dni = dni

            # Recuperar datos ocultos de la API de DNI
            nombres_api = form.cleaned_data.get('nombres_hidden', '').strip()
            paterno_api = form.cleaned_data.get('apellido_paterno_hidden', '').strip()
            materno_api = form.cleaned_data.get('apellido_materno_hidden', '').strip()

            if nombres_api: 
                # CASO A: Si la búsqueda de DNI fue exitosa, usamos los datos precisos
                # Formatear nombres (Ej: "JUAN CARLOS" -> "Juan Carlos")
                user_to_update.first_name = ' '.join(w.capitalize() for w in nombres_api.lower().split())
                
                # Construir apellidos
                apellidos_list = []
                if paterno_api: apellidos_list.append(paterno_api)
                if materno_api: apellidos_list.append(materno_api)
                
                full_lastname = ' '.join(apellidos_list)
                user_to_update.last_name = ' '.join(w.capitalize() for w in full_lastname.lower().split())

            else:
                # CASO B: Fallback (ingreso manual o error de API)
                # Usamos el campo visible 'name' y tratamos de dividirlo
                visible_full_name = form.cleaned_data.get('name', "").strip()
                if visible_full_name:
                    name_parts = visible_full_name.split(' ', 1)
                    user_to_update.first_name = name_parts[0].capitalize()
                    # Si hay más partes, el resto va a apellidos
                    user_to_update.last_name = name_parts[1].title() if len(name_parts) > 1 else ''

        # ---------------------------------------------------------
        # 3. DATOS COMUNES (Teléfono y Dirección)
        # ---------------------------------------------------------
        phone = form.cleaned_data.get('phone_number', '').strip()
        address = form.cleaned_data.get('address', '').strip()

        if hasattr(user_to_update, 'phone_number') and phone:
            user_to_update.phone_number = phone
        
        if hasattr(user_to_update, 'address') and address:
            user_to_update.address = address

        # Guardamos todos los cambios en el perfil del usuario
        user_to_update.save()

        # ---------------------------------------------------------
        # 4. PREPARAR LA INSTANCIA DE LA CITA
        # ---------------------------------------------------------
        # Asignar el usuario logueado (y actualizado) como cliente
        form.instance.client = user_to_update
        
        # Asegurar que el servicio esté asignado (si viene por URL y no por input hidden)
        if not form.instance.service_id and self.kwargs.get('service_id'):
            from django.shortcuts import get_object_or_404
            from services.models import Service
            form.instance.service = get_object_or_404(Service, pk=self.kwargs.get('service_id'))
        response = super().form_valid(form)
        send_appointment_received_email(self.request, self.object)
        # super().form_valid(form) se encarga de hacer form.save() y redirigir
        return response

    def form_invalid(self, form):
        # (Opcional pero recomendado) Mejorar el mensaje de error
        error_list = []
        for field, errors in form.errors.items():
            # Trata de obtener la etiqueta del campo para un mensaje más amigable
            field_label = field
            if field in form.fields:
                field_label = form.fields[field].label or field
            error_list.append(f"{field_label}: {', '.join(errors)}")
        
        if form.non_field_errors():
            error_list.append(f"{_('Errores generales')}: {', '.join(form.non_field_errors())}")

        detailed_error_message = _("Por favor corrige los siguientes errores: ") + "; ".join(error_list)
        messages.error(self.request, detailed_error_message)
        
        return super().form_invalid(form)
    
# --- Búsqueda DNI (Sin cambios, parece independiente) ---
@csrf_exempt # Considera usar autenticación de API si es posible
def buscar_cliente_por_dni(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        if not dni:
            return JsonResponse({'error': 'DNI es requerido'}, status=400)

        token = '685c2d1a88c240a1482b75eed616a993e24e6bfb9b03739853046adf8dfb2863' # ¡Mover a settings!

        try:
            url = f'https://apiperu.dev/api/dni/{dni}?api_token={token}'
            response = requests.get(url, timeout=10) # Añadir timeout

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Devolver más datos si son útiles (nombres, apellidos)
                    return JsonResponse({
                        'nombres': data['data'].get('nombres', ''),
                        'apellidoPaterno': data['data'].get('apellido_paterno', ''),
                        'apellidoMaterno': data['data'].get('apellido_materno', ''),
                        'nombre_completo': data['data'].get('nombre_completo', ''),
                        'dni': data['data'].get('numero', dni),
                    })
                else:
                    error_msg = data.get('message', 'No se encontraron datos.')
                    return JsonResponse({'error': error_msg}, status=404)
            else:
                 return JsonResponse({
                    'error': f'Error en la API externa (Código: {response.status_code})'
                 }, status=response.status_code)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Error de conexión con API externa: {str(e)}'}, status=500)
        except Exception as e:
             # Captura genérica para otros posibles errores (ej. JSON inválido)
            return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# --- Vistas de Lista y Detalle (Ajustadas para LoginRequired y cliente) ---
@login_required(login_url='account_login') # Asegúrate que esta URL exista
def appointment_list(request):
    # Agregamos .exclude(status='cancelled') para que no las traiga
    appointments = Appointment.objects.filter(client=request.user)\
                                      .exclude(status='cancelled')\
                                      .order_by('-appointment_date', '-appointment_time')
    
    context = {'appointments': appointments}
    return render(request, 'appointments/appointment_list.html', context)

@login_required(login_url='account_login')
def appointment_detail(request, appointment_id):
    """Vista para que el cliente vea los detalles de una cita específica suya"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    # Verificar que la cita pertenezca al cliente actual o si es staff
    if appointment.client != request.user and not request.user.is_staff:
         return HttpResponseForbidden(_("No tienes permiso para ver esta cita."))

    context = {'appointment': appointment}
    return render(request, 'appointments/appointment_detail.html', context)


# --- API de Disponibilidades (Reescrita) ---
# Esta versión es básica: solo devuelve las horas generales del día.
# Una versión avanzada generaría slots basados en la duración del servicio
# y las citas ya existentes.
@login_required(login_url='account_login') # O permitir acceso anónimo si es necesario
def get_availabilities(request):
    """
    API básica para obtener el horario laboral general de un día específico.
    """
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Parámetro "date" es requerido'}, status=400)

    try:
        target_date = datetime.date.fromisoformat(date_str)
        workday = ScheduledWorkDay.objects.get(date=target_date)

        if workday.is_working and workday.start_time and workday.end_time:
            # Devolver el rango horario general
             data = {
                 'is_working': True,
                 'start_time': workday.start_time.strftime('%H:%M'),
                 'end_time': workday.end_time.strftime('%H:%M'),
                 'notes': workday.notes
             }
             # --- Lógica Futura: Generación de Slots ---
             # Aquí podrías añadir lógica para generar slots disponibles
             # Necesitarías la duración del servicio (pasada como parámetro?)
             # y consultar las citas ya existentes para ese día/staff.
             # Ejemplo muy básico:
             # slots = generate_time_slots(workday.start_time, workday.end_time, service_duration, existing_appointments)
             # data['available_slots'] = slots
             # ------------------------------------------
        else:
             data = {'is_working': False, 'notes': workday.notes}

        return JsonResponse(data)

    except ScheduledWorkDay.DoesNotExist:
        return JsonResponse({'is_working': False, 'error': 'No schedule defined for this date'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format (YYYY-MM-DD)'}, status=400)
    except Exception as e:
        # Loguear el error real `e` en el servidor
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


# --- Vista request_appointment (Eliminada) ---
# Se elimina esta vista basada en función porque AppointmentRequestView (CBV)
# parece ser la implementación principal y preferida según urls.py
# def request_appointment(request, service_id=None):
#     ... (código anterior eliminado) ...


# --- Vista client_dashboard (Placeholder) ---
# Esta vista fue movida a 'accounts' según urls.py, no debería estar aquí.
# Si necesitas una vista tipo dashboard *dentro* de appointments, créala con otro nombre.
# def client_dashboard(request):
#     # Your logic here
#     return render(request, 'template_name.html')

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Appointment

# appointments/views.py
from .utils import send_appointment_cancelled_email # <--- se importó
@require_POST
@login_required
def cancel_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # CORRECCIÓN AQUÍ: Permitir si es el dueño O si es Staff (Administrador)
    if appointment.client != request.user and not request.user.is_staff:
        messages.error(request, "No tienes permiso para cancelar esta cita.")
        return redirect('appointments:appointment_list')

    # Validar estado
    if appointment.status in ['pending', 'confirmed']:
        appointment.status = 'cancelled'
        appointment.save()
        send_appointment_cancelled_email(request, appointment)
        messages.success(request, "Cita cancelada correctamente.")
    else:
        messages.error(request, "No se puede cancelar una cita completada o ya cancelada.")

    return redirect('appointments:appointment_list')
# ------------------------------------
# en appointments/views.py
def get_daily_availability_status(request):
    # Este endpoint podría devolver un objeto con fechas y su estado (disponible, lleno, no laborable)
    # para un rango de fechas (ej. próximo mes).
    # Por ahora, es un concepto. La implementación detallada dependerá del datepicker.
    data_summary = {}
    today = timezone.now().date()
    one_day_hence = today + datetime.timedelta(days=1)

    # Query para los próximos 30-60 días
    date_range = [one_day_hence + datetime.timedelta(days=i) for i in range(60)]

    for day_to_check in date_range:
        status = "available"
        try:
            workday = ScheduledWorkDay.objects.get(date=day_to_check)
            if not workday.is_working:
                status = "not_working"
        except ScheduledWorkDay.DoesNotExist:
            status = "not_scheduled" # Administrador necesita configurar este día

        if status == "available": # Solo si es laborable y programado, chequear cupos
            count = Appointment.objects.filter(
                appointment_date=day_to_check,
                status__in=['pending', 'confirmed']
            ).count()
            if count >= 3:
                status = "full"
        data_summary[day_to_check.isoformat()] = status

    return JsonResponse(data_summary)

# ... importaciones existentes ...
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt # O usa @login_required si prefieres
def buscar_empresa_por_ruc(request):
    if request.method == 'POST':
        ruc = request.POST.get('ruc')
        if not ruc:
            return JsonResponse({'error': 'RUC es requerido'}, status=400)

        # ⚠️ RECOMENDACIÓN: Mueve esto a settings.py -> settings.DECOLECTA_API_KEY
        token = 'sk_12062.BW7ZrmYioluxNOeo0nKnUQlO6Gs6yAUJ' 
        
        url = f"https://api.decolecta.com/v1/sunat/ruc/full?numero={ruc}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Mapeamos la respuesta de Decolecta a lo que necesita tu frontend
                return JsonResponse({
                    'razon_social': data.get('razon_social'),
                    'direccion': data.get('direccion'),
                    'departamento': data.get('departamento'),
                    'provincia': data.get('provincia'),
                    'distrito': data.get('distrito'),
                    'estado': data.get('estado'),
                    'condicion': data.get('condicion'),
                    'ruc': data.get('numero_documento')
                })
            else:
                return JsonResponse({'error': 'No se encontró el RUC o hubo un error en la API externa.'}, status=404)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Error de conexión: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)