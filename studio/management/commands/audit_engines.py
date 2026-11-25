from django.core.management.base import BaseCommand, CommandError
from studio.universal import SUITES, execute
from collections import Counter

class Command(BaseCommand):
    help = "Run trusted engine audits and fail on missing or failed evidence."

    def add_arguments(self, parser):
        parser.add_argument("suites", nargs="+", choices=tuple(SUITES))

    def handle(self, *args, **options):
        for key in options["suites"]:
            result = execute(key)
            counts = Counter(row["verdict"] for row in result["rows"])
            self.stdout.write(f"{key}: {result['execution']} {dict(counts)}")
            if result["execution"] != "completed" or result["verdict"] != "passed" or counts["passed"] != SUITES[key].checks:
                raise CommandError(result.get("reason", "Engine audit failed"))
