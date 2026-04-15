from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync courses from Google Classroom"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("sync_google_classroom executed"))
