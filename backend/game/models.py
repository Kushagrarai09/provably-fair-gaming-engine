from django.db import models
from decimal import Decimal
class SeedRotation(models.Model):
 STATUS=[("active","Active"),("retired","Retired")]
 server_seed_encrypted=models.TextField()
 server_seed_hash=models.CharField(max_length=64,db_index=True)
 client_seed=models.CharField(max_length=128,default="demo-client-seed")
 next_nonce=models.PositiveBigIntegerField(default=0)
 status=models.CharField(max_length=12,choices=STATUS,default="active")
 created_at=models.DateTimeField(auto_now_add=True)
 revealed_seed=models.CharField(max_length=128,blank=True,default="")
 revealed_at=models.DateTimeField(null=True,blank=True)
class GameRound(models.Model):
 seed_rotation=models.ForeignKey(SeedRotation,on_delete=models.PROTECT,related_name="rounds")
 nonce=models.PositiveBigIntegerField()
 game_type=models.CharField(max_length=12,choices=[("dice","Dice"),("crash","Crash"),("plinko","Plinko")])
 rules_version=models.CharField(max_length=32,default="demo-v1")
 client_seed_snapshot=models.CharField(max_length=128)
 commitment_snapshot=models.CharField(max_length=64)
 outcome=models.JSONField()
 stake=models.DecimalField(max_digits=14,decimal_places=2)
 payout=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0.00"))
 profit=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0.00"))
 idempotency_key=models.CharField(max_length=128,unique=True)
 status=models.CharField(max_length=12,default="pending")
 ledger_reference=models.CharField(max_length=128,blank=True,default="")
 created_at=models.DateTimeField(auto_now_add=True)
 settled_at=models.DateTimeField(null=True,blank=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=["seed_rotation","nonce"],name="unique_seed_nonce")]
  ordering=["-created_at"]
class Wallet(models.Model):
 owner_key=models.CharField(max_length=128,unique=True,default="demo-user")
 balance=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("1000.00"))
 updated_at=models.DateTimeField(auto_now=True)
class LedgerEntry(models.Model):
 idempotency_key=models.CharField(max_length=128,unique=True)
 owner_key=models.CharField(max_length=128,db_index=True)
 amount=models.DecimalField(max_digits=14,decimal_places=2)
 entry_type=models.CharField(max_length=24)
 reference=models.CharField(max_length=128)
 created_at=models.DateTimeField(auto_now_add=True)
