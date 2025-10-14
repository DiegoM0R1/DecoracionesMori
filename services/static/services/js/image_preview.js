
document.addEventListener('DOMContentLoaded', function() {
    // Función para configurar el listener en un campo de entrada de archivo
    function setupImagePreview(fileInput) {
        // Buscamos el elemento de vista previa relativo al campo de archivo
        const formRow = fileInput.closest('.form-row');
        if (!formRow) return;

        const previewImage = formRow.querySelector('.image-preview-widget');
        if (!previewImage) return;

        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    previewImage.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Selector actualizado para encontrar todos los inputs de tipo "file"
    // que estén dentro del formulario principal del admin de Django.
    function initializePreviews() {
        document.querySelectorAll('#content-main input[type=file]').forEach(setupImagePreview);
    }
    
    // Inicializar para los campos que ya existen al cargar
    initializePreviews();
    
    // Escuchar cuando Django añade un nuevo formulario inline
    document.addEventListener('formset:added', function(event) {
        const newRow = event.target;
        const fileInput = newRow.querySelector('input[type=file]');
        if (fileInput) {
            setupImagePreview(fileInput);
        }
    });
});