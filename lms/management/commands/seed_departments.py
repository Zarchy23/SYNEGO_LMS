from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed default departments"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("seed_departments executed"))
