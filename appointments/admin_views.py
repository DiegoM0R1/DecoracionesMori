# appointments/admin_views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods # No usado directamente aquí, pero puede ser útil
from django.utils import timezone
from django.db.models import Count
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta, time
import json

from .models import Appointment, ScheduledWorkDay, WorkScheduleTemplate
from services.models import Service # Asegúrate que esta app y modelo existan
from django.contrib.auth import get_user_model

User = get_user_model()

@staff_member_required
def calendar_events_api(request):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    service_filter = request.GET.get('service')
    staff_filter = request.GET.get('staff')

    if not start_str or not end_str:
        return JsonResponse({'error': 'Start and end dates required'}, status=400)

    try:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    events = []
    current_date = start_date
    while current_date <= end_date:
        try:
            workday = ScheduledWorkDay.objects.get(date=current_date)
            if workday.is_working and workday.start_time and workday.end_time:
                events.append({
                    'id': f'workday-{current_date}',
                    'title': f'Horario: {workday.start_time.strftime("%H:%M")} - {workday.end_time.strftime("%H:%M")}',
                    'start': current_date.isoformat(), 'end': current_date.isoformat(),
                    'display': 'background', 'backgroundColor': '#e8f5e8', 'borderColor': '#4caf50',
                    'classNames': ['workday-event']
                })
            elif not workday.is_working:
                events.append({
                    'id': f'non-workday-{current_date}', 'title': 'Día no laborable',
                    'start': current_date.isoformat(), 'end': current_date.isoformat(),
                    'display': 'background', 'backgroundColor': '#ffebee', 'borderColor': '#f44336',
                    'classNames': ['non-workday-event']
                })
        except ScheduledWorkDay.DoesNotExist:
            day_of_week = current_date.weekday()
            try:
                template = WorkScheduleTemplate.objects.get(day_of_week=day_of_week)
                if template.is_working_day and template.start_time and template.end_time:
                    events.append({
                        'id': f'template-{current_date}',
                        'title': f'Plantilla: {template.start_time.strftime("%H:%M")} - {template.end_time.strftime("%H:%M")}',
                        'start': current_date.isoformat(), 'end': current_date.isoformat(),
                        'display': 'background', 'backgroundColor': '#fff3e0', 'borderColor': '#ff9800',
                        'classNames': ['template-event']
                    })
            except WorkScheduleTemplate.DoesNotExist:
                pass
        current_date += timedelta(days=1)

    appointments_query = Appointment.objects.filter(
        appointment_date__range=[start_date, end_date],
        appointment_date__isnull=False, appointment_time__isnull=False
    ).select_related('client', 'service', 'staff')

    if service_filter and service_filter != 'all':
        appointments_query = appointments_query.filter(service_id=service_filter)
    if staff_filter and staff_filter != 'all':
        appointments_query = appointments_query.filter(staff_id=staff_filter)

    status_colors = {'pending': '#ffc107', 'confirmed': '#28a745', 'completed': '#6c757d', 'cancelled': '#dc3545'}
    for appt in appointments_query:
        start_dt = datetime.combine(appt.appointment_date, appt.appointment_time)
        duration = getattr(appt.service, 'duration', 60)
        end_dt = start_dt + timedelta(minutes=duration)
        client_name = appt.client.get_full_name() or appt.client.username
        staff_name = appt.staff.get_full_name() if appt.staff else 'Sin asignar'
        events.append({
            'id': f'appointment-{appt.id}',
            'title': f'{client_name} - {appt.service.name}',
            'start': start_dt.isoformat(), 'end': end_dt.isoformat(),
            'backgroundColor': status_colors.get(appt.status, '#6c757d'),
            'borderColor': status_colors.get(appt.status, '#6c757d'),
            'textColor': '#ffffff',
            'extendedProps': {
                'appointmentId': appt.id, 'clientName': client_name, 'serviceName': appt.service.name,
                'staffName': staff_name, 'status': appt.status, 'statusDisplay': appt.get_status_display(),
                'phone': getattr(appt.client, 'phone_number', ''), 'notes': appt.notes, 'type': 'appointment'
            },
            'classNames': ['appointment-event', f'status-{appt.status}']
        })
    return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)

@staff_member_required
def update_appointment_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required.'}, status=405)
    try:
        data = json.loads(request.body)
        appt_id = data.get('id', '').replace('appointment-', '')
        if not appt_id: return JsonResponse({'error': 'ID de cita requerido'}, status=400)
        
        appointment = get_object_or_404(Appointment, id=appt_id)
        if 'start' in data:
            new_dt = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
            appointment.appointment_date = new_dt.date()
            appointment.appointment_time = new_dt.time()
        if 'status' in data: appointment.status = data['status']
        appointment.save()
        return JsonResponse({'success': True, 'message': 'Cita actualizada'})
    except json.JSONDecodeError: return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Appointment.DoesNotExist: return JsonResponse({'error': 'Cita no encontrada'}, status=404)
    except Exception as e: return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
def appointment_stats_api(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_month = today.replace(day=1)
    stats = {
        'today': {'total': Appointment.objects.filter(appointment_date=today).count()},
        'week': {'total': Appointment.objects.filter(appointment_date__range=[start_of_week, end_of_week]).count()},
        'month': {'total': Appointment.objects.filter(appointment_date__range=[start_of_month, today]).count()}
    }
    return JsonResponse(stats, encoder=DjangoJSONEncoder)

@staff_member_required
def workday_schedule_api(request):
    if request.method == 'GET':
        date_str = request.GET.get('date')
        if not date_str: return JsonResponse({'error': 'Fecha requerida'}, status=400)
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            workday = ScheduledWorkDay.objects.get(date=target_date)
            return JsonResponse({
                'date': workday.date.isoformat(),
                'start_time': workday.start_time.strftime('%H:%M') if workday.start_time else None,
                'end_time': workday.end_time.strftime('%H:%M') if workday.end_time else None,
                'is_working': workday.is_working, 'notes': workday.notes
            })
        except ScheduledWorkDay.DoesNotExist:
            day_of_week = target_date.weekday()
            try:
                template = WorkScheduleTemplate.objects.get(day_of_week=day_of_week)
                return JsonResponse({
                    'date': target_date.isoformat(),
                    'start_time': template.start_time.strftime('%H:%M') if template.start_time else None,
                    'end_time': template.end_time.strftime('%H:%M') if template.end_time else None,
                    'is_working': template.is_working_day, 'notes': '', 'from_template': True
                })
            except WorkScheduleTemplate.DoesNotExist:
                return JsonResponse({'date': target_date.isoformat(), 'start_time': None, 'end_time': None,
                                     'is_working': True, 'notes': '', 'not_configured': True })
        except ValueError: return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            workday, created = ScheduledWorkDay.objects.get_or_create(date=target_date, defaults={
                'is_working': data.get('is_working', True),
                'start_time': datetime.strptime(data['start_time'], '%H:%M').time() if data.get('start_time') else None,
                'end_time': datetime.strptime(data['end_time'], '%H:%M').time() if data.get('end_time') else None,
                'notes': data.get('notes', '')
            })
            if not created:
                workday.is_working = data.get('is_working', workday.is_working)
                workday.start_time = datetime.strptime(data['start_time'], '%H:%M').time() if data.get('start_time') else None
                workday.end_time = datetime.strptime(data['end_time'], '%H:%M').time() if data.get('end_time') else None
                workday.notes = data.get('notes', workday.notes)
                workday.save()
            return JsonResponse({'success': True, 'message': 'Horario actualizado'})
        except json.JSONDecodeError: return JsonResponse({'error': 'JSON inválido'}, status=400)
        except ValueError as e: return JsonResponse({'error': f'Error en formato de datos: {str(e)}'}, status=400)
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)