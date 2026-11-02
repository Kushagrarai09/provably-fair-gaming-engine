from django.contrib import admin
from .models import SeedRotation,GameRound,Wallet,LedgerEntry
admin.site.register([SeedRotation,GameRound,Wallet,LedgerEntry])
