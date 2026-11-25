from django.core.management.base import BaseCommand, CommandError
from studio import chain, engine

class Command(BaseCommand):
    help = "Check testnet identity and execute all trusted Gno transfer cases."

    def handle(self, *args, **options):
        try:
            self.stdout.write(str(chain.status("testnet")))
            for name, family, balance, amount, authorized, status, final in engine.CASES:
                observed, evidence = engine.execute({"balance":balance,"amount":amount,"authorized":authorized})
                if observed != {"status":status,"balance":final,"state_changed":final != balance}:
                    raise RuntimeError("Unexpected result: " + name)
                self.stdout.write(self.style.SUCCESS(name + ": PASS"))
        except Exception as exc:
            raise CommandError(str(exc)) from exc
