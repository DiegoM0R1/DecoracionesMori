from django.db import models

# Create your models here.
from django.db import models

class ReporteDummy(models.Model):
    """
    Modelo dummy solo para que Jazzmin muestre la app en el menú.
    No se usará realmente, solo existe para engañar al admin.
    """
    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        managed = False  # No crear tabla en la BD
        db_table = 'reports_dummy'  # Tabla que nunca se creará
    
    def __str__(self):
        return "Reportes"