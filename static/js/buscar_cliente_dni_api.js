document.addEventListener('DOMContentLoaded', function() {
    // Depuración de selectores
    console.log('Buscando elementos del DOM');
    console.log('Botón de búsqueda:', document.getElementById('buscarDniBtn'));
    console.log('Input DNI:', document.getElementById('id_dni'));
    console.log('Input Nombre:', document.getElementById('id_name'));

    const buscarDniBtn = document.getElementById('buscarDniBtn');
    const dniInput = document.getElementById('id_dni');
    const nameInput = document.getElementById('id_name');

    // Verificar si los elementos existen
    if (!buscarDniBtn || !dniInput || !nameInput) {
        console.error('Uno o más elementos no encontrados:',
            'Botón:', buscarDniBtn,
            'Input DNI:', dniInput,
            'Input Nombre:', nameInput
        );
        return;
    }

    buscarDniBtn.addEventListener('click', function() {
        const dni = dniInput.value.trim();
        
        console.log('DNI a buscar:', dni);

        // Validaciones
        if (!dni) {
            alert('Por favor, ingrese un DNI');
            return;
        }

        if (dni.length !== 8) {
            alert('El DNI debe tener 8 dígitos');
            return;
        }

        // Obtener el token CSRF
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        console.log('Realizando fetch con DNI:', dni);

        // Realizar la búsqueda
        fetch('{% url "appointments:buscar_dni" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: new URLSearchParams({
                'dni': dni
            })
        })
        .then(response => {
            console.log('Respuesta recibida:', response);
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);

            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Rellenar el campo de nombre si se encuentra
            if (data.nombre) {
                // Convertir el nombre a título (primera letra de cada palabra en mayúscula)
                const nombreFormateado = data.nombre
                    .toLowerCase()
                    .split(' ')
                    .map(palabra => palabra.charAt(0).toUpperCase() + palabra.slice(1))
                    .join(' ');
                
                console.log('Nombre formateado:', nombreFormateado);
                nameInput.value = nombreFormateado;
                
                // Añadir retroalimentación visual
                nameInput.classList.add('is-valid');
                setTimeout(() => {
                    nameInput.classList.remove('is-valid');
                }, 3000);
            } else {
                alert('No se encontró información para este DNI');
            }
        })
        .catch(error => {
            console.error('Error completo:', error);
            alert('Error al buscar el DNI');
        });
    });
});
