from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from invoices.models import InvoiceItem
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
import json
from django.core.serializers.json import DjangoJSONEncoder

import csv
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS # ¡Necesitarás instalarla!
from django.conf import settings
from django.contrib import admin
@staff_member_required

def sales_report_view(request):
    # --- 1. Rango de Fechas (Sin cambios) ---
    today = timezone.now().date()
    range_preset = request.GET.get('range', 'month') 
    start_date = today.replace(day=1)
    end_date = today
    # ... (lógica para day, week, custom sin cambios) ...
    if range_preset == 'day':
        start_date = today
    elif range_preset == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif range_preset == 'custom':
        start_date_str = request.GET.get('start')
        end_date_str = request.GET.get('end')
        if start_date_str and end_date_str:
            try: # Añadir try-except por si las fechas son inválidas
                start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                # Si las fechas son inválidas, volvemos al mes actual
                start_date = today.replace(day=1)
                end_date = today
                range_preset = 'month' # Actualizar preset para reflejar la fallback


    # --- 2. Query Principal (Modificada) ---
    sales_items = InvoiceItem.objects.filter(
        invoice__status='pagada',
        item_type='service',
        invoice__date_issued__range=[start_date, end_date]
    ).select_related('service')

    # Agrupar y anotar datos
    report_data_aggregated = sales_items.values(
        'service__name'
    ).annotate(
        total_sold=Count('id'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue') # Mantenemos el orden por ingresos

    # --- 3. Calcular Totales Generales ---
    grand_total_sold = report_data_aggregated.aggregate(Sum('total_sold'))['total_sold__sum'] or 0
    grand_total_revenue = report_data_aggregated.aggregate(Sum('total_revenue'))['total_revenue__sum'] or Decimal('0.00')

    # --- 4. Calcular Detalles Adicionales (Precio Promedio y Porcentaje) ---
    report_data_detailed = []
    for item in report_data_aggregated:
        quantity = item['total_sold']
        revenue = item['total_revenue']
        
        # Evitar división por cero
        avg_price = (revenue / quantity) if quantity > 0 else Decimal('0.00')
        revenue_percentage = (revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else Decimal('0.00')
        
        report_data_detailed.append({
            'service_name': item['service__name'],
            'total_sold': quantity,
            'total_revenue': revenue,
            'average_price': avg_price,
            'revenue_percentage': revenue_percentage,
        })

    # --- 5. Datos para FullCalendar (Sin cambios) ---
    calendar_events = sales_items.annotate(
        date=TruncDay('invoice__date_issued')
    ).values(
        'date', 'service__name'
    ).annotate(
        count=Count('id')
    ).order_by('date')
    
    events_list = []
    for event in calendar_events:
         events_list.append({
            'title': f"{event['count']}x {event['service__name']}",
            'start': event['date'],
            'allDay': True
         })

    # --- 6. Contexto Actualizado ---
    context = {
        'title': 'Reporte de Ventas de Servicios',
        'report_data': report_data_detailed, # Usamos la lista detallada
        'grand_total_sold': grand_total_sold,
        'grand_total_revenue': grand_total_revenue,
        'calendar_events': json.dumps(events_list, cls=DjangoJSONEncoder),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'range_preset': range_preset,
        'has_permission': True 
    }
    
    admin_context = admin.site.each_context(request) 
    context.update(admin_context) 

    return render(request, 'admin/reports/sales_report.html', context)

# --- Actualizar get_report_data para las descargas ---
def get_report_data(start, end):
    """Función helper para obtener datos detallados para descargas"""
    sales_items = InvoiceItem.objects.filter(
        invoice__status='pagada',
        item_type='service',
        invoice__date_issued__range=[start, end]
    ).select_related('service')

    report_data_aggregated = sales_items.values(
        'service__name'
    ).annotate(
        total_sold=Count('id'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')

    grand_total_revenue = report_data_aggregated.aggregate(Sum('total_revenue'))['total_revenue__sum'] or Decimal('0.00')

    report_data_detailed = []
    for item in report_data_aggregated:
        quantity = item['total_sold']
        revenue = item['total_revenue']
        avg_price = (revenue / quantity) if quantity > 0 else Decimal('0.00')
        revenue_percentage = (revenue / grand_total_revenue * 100) if grand_total_revenue > 0 else Decimal('0.00')
        
        report_data_detailed.append({
            'service_name': item['service__name'],
            'total_sold': quantity,
            'total_revenue': revenue,
            'average_price': avg_price,
            'revenue_percentage': revenue_percentage,
        })
    # Devuelve también los totales generales para usarlos en el PDF/CSV si es necesario
    grand_total_sold = sum(item['total_sold'] for item in report_data_detailed)
    return report_data_detailed, grand_total_sold, grand_total_revenue

def get_date_range(request):
    """Función helper para obtener fechas"""
    today = timezone.now().date()
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if start_date and end_date:
        start = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        end = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        return start, end
    else:
        # Fallback si no hay fechas (ej. mes actual)
        range_preset = request.GET.get('range', 'month')
        if range_preset == 'day':
            return today, today
        if range_preset == 'week':
            start = today - timedelta(days=today.weekday())
            return start, today
        # Default: month
        start = today.replace(day=1)
        return start, today


@staff_member_required
def download_csv_view(request):
    start_date, end_date = get_date_range(request)
    # --- Obtener datos detallados y totales ---
    report_data, grand_total_sold, grand_total_revenue = get_report_data(start_date, end_date)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{start_date}_a_{end_date}.csv"'
    
    writer = csv.writer(response)
    # Encabezados actualizados
    writer.writerow(['Servicio', 'Cantidad Vendida', 'Ingresos Totales (S/)', 'Precio Promedio (S/)', '% Ingresos'])
    
    # Datos
    for item in report_data:
        writer.writerow([
            item['service_name'], 
            item['total_sold'], 
            f"{item['total_revenue']:.2f}", # Formatear decimal
            f"{item['average_price']:.2f}",
            f"{item['revenue_percentage']:.2f}%" 
        ])
    
    # Fila de Totales
    writer.writerow([]) # Linea en blanco
    writer.writerow(['TOTAL', grand_total_sold, f"{grand_total_revenue:.2f}", '', '100.00%'])
        
    return response

@staff_member_required
def download_pdf_view(request):
    start_date, end_date = get_date_range(request)
    # --- Obtener datos detallados y totales ---
    report_data, grand_total_sold, grand_total_revenue = get_report_data(start_date, end_date)
    
    context = {
        'report_data': report_data,
        'grand_total_sold': grand_total_sold,
        'grand_total_revenue': grand_total_revenue,
        'start_date': start_date,
        'end_date': end_date,
        # site_settings se inyecta automáticamente
    }
    
    html_string = render_to_string('admin/reports/report_pdf.html', context)
    
    # Mismo CSS que antes
    css = CSS(string="""
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Helvetica', sans-serif; font-size: 10pt;}
        h1 { text-align: center; color: #333; margin-bottom: 0.5cm;}
        .logo { max-width: 150px; max-height: 50px; height: auto; position: absolute; top: 1cm; left: 1cm; }
        .company-info { position: absolute; top: 1cm; right: 1cm; text-align: right; font-size: 9pt; color: #555;}
        table { width: 100%; border-collapse: collapse; margin-top: 1cm; } /* Reducido margen superior */
        th, td { border: 1px solid #ccc; padding: 6px; text-align: left; } /* Menos padding */
        th { background-color: #f0f0f0; font-weight: bold; }
        .footer { position: fixed; bottom: 1cm; left: 0; right: 0; text-align: center; font-size: 8pt; color: #777;}
        /* Estilos para la fila de totales */
        tfoot td { font-weight: bold; background-color: #f0f0f0; } 
        /* Alinear números a la derecha */
        td:nth-child(2), td:nth-child(3), td:nth-child(4), td:nth-child(5) { text-align: right; }
        th:nth-child(2), th:nth-child(3), th:nth-child(4), th:nth-child(5) { text-align: right; }
    """)
    
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{start_date}_a_{end_date}.pdf"'
    return response

