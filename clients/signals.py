from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ClientProfile  # Asegúrate que ClientProfile está en clients.models

User = get_user_model() # Obtiene el modelo User activo (tu User personalizado)

@receiver(post_save, sender=User)
def manage_client_profile_for_user(sender, instance, **kwargs):
    """
    Crea o elimina automáticamente un ClientProfile basado en el estado 'is_staff' del usuario.

    - Si un usuario NO es staff (instance.is_staff == False):
      Se asegura de que exista un ClientProfile para este usuario.
      Si no existe, se crea uno. El campo 'client_type' usará el valor por defecto
      definido en el modelo ClientProfile (que es 'prospect').

    - Si un usuario ES staff (instance.is_staff == True):
      Se asegura de que NO exista un ClientProfile para este usuario.
      Si existe alguno, se elimina.
    """
    if hasattr(instance, 'is_staff'): # Buena práctica verificar que el atributo existe
        if not instance.is_staff:
            # El usuario NO es staff.
            # get_or_create intenta obtener el ClientProfile y si no existe, lo crea.
            # Utilizará el valor 'prospect' por defecto para client_type definido en tu modelo ClientProfile.
            profile, created = ClientProfile.objects.get_or_create(user=instance)
            # if created:
            #     print(f"ClientProfile creado para el usuario no-staff: {instance.username}")
            # else:
            #     print(f"ClientProfile ya existía para el usuario no-staff: {instance.username}")
        else:
            # El usuario ES staff.
            # Se busca y elimina cualquier ClientProfile asociado a este usuario.
            # filter().delete() no lanza error si no encuentra objetos, lo cual es conveniente.
            ClientProfile.objects.filter(user=instance).delete()
            # if count > 0:
            #    print(f"ClientProfile eliminado para el usuario staff: {instance.username}")
    else:
        # Este caso no debería ocurrir si 'instance' es un modelo User estándar de Django
        # o uno que herede de AbstractUser.
        print(f"Advertencia: La instancia de usuario {instance} no tiene el atributo 'is_staff'.")