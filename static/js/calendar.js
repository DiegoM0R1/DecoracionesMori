// static/js/calendar.js
document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    if (!calendarEl) return;
    
    // Get available slots from the data attribute
    const availabilityData = JSON.parse(calendarEl.dataset.availability || '[]');
    
    // Transform data for FullCalendar
    const events = availabilityData.map(slot => ({
        title: `Available: ${slot.start_time} - ${slot.end_time}`,
        start: `${slot.date}T${slot.start_time}`,
        end: `${slot.date}T${slot.end_time}`,
        extendedProps: {
            staffId: slot.staff_id,
            availabilityId: slot.id
        },
        backgroundColor: '#28a745',
        borderColor: '#28a745'
    }));
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        events: events,
        eventClick: function(info) {
            // When a slot is clicked
            const availabilityId = info.event.extendedProps.availabilityId;
            document.getElementById('selectedAvailabilityId').value = availabilityId;
            
            // Update the selected time text
            const startTime = info.event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const endTime = info.event.end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const dateStr = info.event.start.toLocaleDateString();
            
            document.getElementById('selectedTimeText').textContent = 
                `${dateStr} from ${startTime} to ${endTime}`;
            
            // Show the confirmation section
            document.getElementById('timeSelectionConfirmation').classList.remove('d-none');
            
            // Scroll to the confirmation section
            document.getElementById('timeSelectionConfirmation').scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
    
    calendar.render();
});