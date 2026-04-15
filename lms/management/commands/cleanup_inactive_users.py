from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cleanup inactive users"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("cleanup_inactive_users executed"))
