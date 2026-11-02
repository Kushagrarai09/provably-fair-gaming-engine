from rest_framework import serializers
from decimal import Decimal
class ClientSeedSerializer(serializers.Serializer):
 client_seed=serializers.CharField(min_length=1,max_length=128)
class DicePlaySerializer(serializers.Serializer):
 stake=serializers.DecimalField(max_digits=12,decimal_places=2,min_value=Decimal("0.01"),max_value=Decimal("100000"))
 target=serializers.IntegerField(min_value=1,max_value=98)
class CrashPlaySerializer(serializers.Serializer):
 stake=serializers.DecimalField(max_digits=12,decimal_places=2,min_value=Decimal("0.01"),max_value=Decimal("100000"))
 cashout_at=serializers.DecimalField(max_digits=7,decimal_places=2,min_value=Decimal("1.01"),max_value=Decimal("1000"))
class PlinkoPlaySerializer(serializers.Serializer):
 stake=serializers.DecimalField(max_digits=12,decimal_places=2,min_value=Decimal("0.01"),max_value=Decimal("100000"))
 rows=serializers.IntegerField(min_value=8,max_value=16,default=12)
 risk=serializers.ChoiceField(choices=["low","medium","high"],default="medium")
class VerifySerializer(serializers.Serializer):
 server_seed=serializers.CharField(min_length=1,max_length=128)
 commitment=serializers.CharField(min_length=64,max_length=64)
 client_seed=serializers.CharField(min_length=1,max_length=128)
 nonce=serializers.IntegerField(min_value=0)
 game_type=serializers.ChoiceField(choices=["dice","crash","plinko"])
 expected_outcome=serializers.JSONField(required=False)
