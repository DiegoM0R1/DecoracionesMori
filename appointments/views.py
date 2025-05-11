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
# ... otras importaciones ...
User = get_user_model() # En lugar de User = settings.AUTH_USER_MODEL

# --- Vista de Calendario (Simplificada o requiere JS pesado) ---
# Esta vista necesita una redefinición completa.
# Podría mostrar los ScheduledWorkDay o necesitar JS para mostrar slots.
# Por ahora, la dejamos comentada o muy básica.
# class AppointmentCalendarView(LoginRequiredMixin, ListView):
#     template_name = 'appointments/calendar.html'
#     model = ScheduledWorkDay # Mostrar días laborables generales?
#     context_object_name = 'work_days'
#
#     def get_queryset(self):
#         # Mostrar días laborables futuros
#         return ScheduledWorkDay.objects.filter(
#             date__gte=timezone.now().date(),
#             is_working=True
#         ).order_by('date')
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['service_id'] = self.request.GET.get('service') # Pasar service_id si es relevante
#         # Aquí necesitarías pasar datos para un calendario JS (FullCalendar, etc.)
#         return context


# --- Vista de Solicitud de Cita (Principal) ---
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
        Procesar el formulario válido:
        1. Actualizar el perfil del usuario logueado con datos del formulario.
        2. Asignar el usuario como cliente de la cita.
        3. Guardar la cita.
        """
        user_to_update = self.request.user

        # --- Actualización de Nombre y Apellidos usando campos ocultos ---
        nombres_capturados = form.cleaned_data.get('nombres_hidden', '').strip()
        paterno_capturado = form.cleaned_data.get('apellido_paterno_hidden', '').strip()
        materno_capturado = form.cleaned_data.get('apellido_materno_hidden', '').strip()

        # Usar los nombres capturados del DNI para first_name
        # y la combinación de apellidos para last_name.
        if nombres_capturados: # Si la búsqueda de DNI llenó estos campos
            # Formatear a Title Case (primera letra mayúscula en cada palabra)
            formatted_first_name = ' '.join(word.capitalize() for word in nombres_capturados.lower().split())
            
            surnames_list = []
            if paterno_capturado:
                surnames_list.append(' '.join(word.capitalize() for word in paterno_capturado.lower().split()))
            if materno_capturado:
                surnames_list.append(' '.join(word.capitalize() for word in materno_capturado.lower().split()))
            formatted_last_name = ' '.join(surnames_list).strip()

            if user_to_update.first_name != formatted_first_name or \
               user_to_update.last_name != formatted_last_name:
                user_to_update.first_name = formatted_first_name
                user_to_update.last_name = formatted_last_name
        else:
            # Fallback: Si los campos ocultos del DNI están vacíos (ej. DNI no encontrado o no ingresado),
            # usar el valor del campo de nombre visible (que el usuario podría haber llenado manualmente).
            visible_full_name = form.cleaned_data.get('name', "").strip()
            if visible_full_name:
                name_parts = visible_full_name.split(' ', 1)
                # Asignación simple: primera palabra a nombres, resto a apellidos.
                user_to_update.first_name = name_parts[0].capitalize() # Solo la primera palabra capitalizada
                user_to_update.last_name = ' '.join(word.capitalize() for word in (name_parts[1] if len(name_parts) > 1 else '').lower().split())

        
        # DNI (asumiendo que tu modelo User tiene un campo 'dni')
        form_dni = form.cleaned_data.get('dni', "").strip()
        if hasattr(user_to_update, 'dni'): # Comprueba si el usuario tiene el atributo dni
            if user_to_update.dni != form_dni:
                user_to_update.dni = form_dni
        
        # Teléfono (asumiendo que tu modelo User tiene un campo 'phone_number')
        form_phone_number = form.cleaned_data.get('phone_number', "").strip()
        if hasattr(user_to_update, 'phone_number'):
            if user_to_update.phone_number != form_phone_number:
                user_to_update.phone_number = form_phone_number
        
        # Dirección (asumiendo que tu modelo User tiene un campo 'address')
        form_address = form.cleaned_data.get('address', "").strip()
        if hasattr(user_to_update, 'address'):
            if user_to_update.address != form_address:
                user_to_update.address = form_address
        
        user_to_update.save() # Guardar todos los cambios en el perfil del usuario

        # 2. Preparar la instancia de la cita
        form.instance.client = user_to_update # Asignar el cliente (usuario logueado)

        # Asegurar que el servicio está asignado (el form debería manejarlo con HiddenInput e initial)
        if not form.instance.service and self.kwargs.get('service_id'):
             form.instance.service = get_object_or_404(Service, pk=self.kwargs.get('service_id'))
        
        # 3. Dejar que CreateView guarde la cita y maneje la redirección.
        # super().form_valid(form) llamará a form.save() (que guarda form.instance)
        # y luego redirigirá usando get_success_url().
        # El mensaje de éxito se ha movido a get_success_url.
        return super().form_valid(form)

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

        token = 'de3e5dc9486d29e79d5d497fa4082ba9f18472e6a1ec9686de1e35e6c0be81d7' # ¡Mover a settings!

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
    """Lista de todas las citas del cliente logueado"""
    appointments = Appointment.objects.filter(client=request.user).order_by('-appointment_date', '-appointment_time')
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

# --- ASEGÚRATE QUE ESTA VISTA EXISTA ---
@require_POST # Solo permite método POST
@login_required(login_url='account_login') # Usuario debe estar logueado
def cancel_appointment_view(request, appointment_id):
    # Busca la cita
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Verifica permisos: ¿Es el cliente de la cita o un miembro del staff?
    if appointment.client != request.user and not request.user.is_staff:
        messages.error(request, _("No tienes permiso para cancelar esta cita."))
        # Redirige a la lista o a donde corresponda
        return redirect('appointments:appointment_list')

    # Verifica si el estado actual permite la cancelación
    allowed_statuses = ['pending', 'confirmed'] # Define qué estados se pueden cancelar
    if appointment.status in allowed_statuses:
        appointment.status = 'cancelled' # Cambia el estado
        appointment.save()             # Guarda el cambio
        messages.success(request, _("La cita #{id} ha sido cancelada.").format(id=appointment.id))
    else:
        messages.warning(request, _("Esta cita ya no se puede cancelar (Estado: {status}).").format(status=appointment.get_status_display()))

    # Redirige de vuelta a la página de detalle de la cita (ahora cancelada)
    # o a la lista de citas. Redirigir al detalle es útil para ver el cambio.
    return redirect('appointments:appointment_detail', appointment_id=appointment.id)
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

