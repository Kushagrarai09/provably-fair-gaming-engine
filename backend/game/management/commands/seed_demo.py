from django.core.management.base import BaseCommand
from game.views import active_seed
from game.ledger import wallet_snapshot
class Command(BaseCommand):
 def handle(self,*args,**kwargs):
  s=active_seed();w=wallet_snapshot()
  self.stdout.write(self.style.SUCCESS(f"Commitment: {s.server_seed_hash}; wallet: {w.balance} VC"))
