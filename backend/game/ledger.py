import os
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from .models import Wallet,LedgerEntry
class LedgerError(Exception): pass
def wallet_snapshot(owner="demo-user"):
 w,_=Wallet.objects.get_or_create(owner_key=owner,defaults={"balance":Decimal("1000.00")})
 return w
@transaction.atomic
def apply_delta(owner,amount,key,entry_type,reference):
 old=LedgerEntry.objects.filter(idempotency_key=key).first()
 if old: return wallet_snapshot(owner),old,True
 w=Wallet.objects.select_for_update().filter(owner_key=owner).first()
 if not w: w=Wallet.objects.create(owner_key=owner,balance=Decimal("1000.00"))
 amount=Decimal(amount).quantize(Decimal("0.01"))
 if amount<0 and w.balance<abs(amount): raise LedgerError("Insufficient virtual-credit balance.")
 LedgerEntry.objects.create(idempotency_key=key,owner_key=owner,amount=amount,entry_type=entry_type,reference=reference)
 Wallet.objects.filter(pk=w.pk).update(balance=F("balance")+amount)
 w.refresh_from_db()
 return w,LedgerEntry.objects.get(idempotency_key=key),False
def assert_remote_adapter_ready():
 if os.getenv("LEDGER_MODE","local").lower()=="playledger":
  if not(os.getenv("PLAYLEDGER_BASE_URL") and os.getenv("PLAYLEDGER_API_TOKEN")):
   raise LedgerError("Configure PLAYLEDGER_BASE_URL and PLAYLEDGER_API_TOKEN.")
  raise LedgerError("Remote adapter intentionally fails closed until mapped and tested against your PlayLedger API contract.")
