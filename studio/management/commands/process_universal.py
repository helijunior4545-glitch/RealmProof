import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from studio.universal_queue import process_one

class Command(BaseCommand):
    help = "Process trusted universal test jobs. Use one worker with SQLite."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            if not process_one():
                if not options["watch"]:
                    break
                time.sleep(2)
