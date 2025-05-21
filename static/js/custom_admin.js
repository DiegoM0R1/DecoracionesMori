/**
 * Script personalizado para el panel de administración de DecoracionesMori
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin personalizado cargado correctamente');
    
    // Solución para el problema de dark_mode_theme
    if (document.querySelector('.login')) {
        // Estamos en la página de login
        const body = document.body;
        // Añadir clase de modo claro por defecto si no existe configuración de tema oscuro
        if (!body.classList.contains('dark-mode') && !body.classList.contains('light-mode')) {
            body.classList.add('light-mode');
        }
    }
    
    // Mejoras visuales para el panel de administración
    const adminBranding = document.querySelector('.site-name');
    if (adminBranding) {
        adminBranding.innerHTML = 'Decoraciones Mori <small>Panel de Administración</small>';
    }
});