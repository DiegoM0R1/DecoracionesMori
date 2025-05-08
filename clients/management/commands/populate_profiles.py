# clients/management/commands/populate_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clients.models import ClientProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates ClientProfile for existing non-staff users missing one.'

    def handle(self, *args, **options):
        users_needing_profile = User.objects.filter(is_staff=False, client_profile__isnull=True)
        count = 0
        for user in users_needing_profile:
            ClientProfile.objects.create(user=user) # Se crea el perfil
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {count} ClientProfile(s).'))