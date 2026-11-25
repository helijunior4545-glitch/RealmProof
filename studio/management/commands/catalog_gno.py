from django.core.management.base import BaseCommand
from studio.native_catalog import inventory, summarize
import json
class Command(BaseCommand):
    help = "Inventory trusted installed Gno reference tests without executing them."
    def handle(self, *args, **options):
        rows, truncated = inventory()
        self.stdout.write(json.dumps({"metrics":summarize(rows),"truncated":truncated}, indent=2))
