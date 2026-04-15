from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send daily reminders to users"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("send_daily_reminders executed"))
