import time
from django.core.management import BaseCommand
from django.db import connection, OperationalError


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_connection = False
        counter = 0
        while not db_connection:
            if counter >= 60:
                break
            try:
                connection.ensure_connection()
                db_connection = True
            except OperationalError:
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)
                counter += 1
        self.stdout.write(self.style.SUCCESS("Database available!"))
