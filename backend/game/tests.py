from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from .fairness import *
from .models import GameRound,Wallet
class FairnessTests(TestCase):
 def test_commitment_and_verifier(self):
  s="server-seed";self.assertEqual(len(commitment(s)),64)
  self.assertTrue(verify(s,commitment(s),"client",0,"dice")["valid"])
 def test_dice_bounds_deterministic(self):
  x=dice_result("s","c",3);self.assertEqual(x,dice_result("s","c",3));self.assertTrue(0<=x<10000)
 def test_crash_bounds(self):
  self.assertTrue(all(100<=crash_multiplier_x100("s","c",n)<=100000 for n in range(20)))
 def test_plinko(self):
  self.assertEqual(len(plinko_path("s","c",1,12)),12)
  self.assertEqual(plinko_path("s","c",1,12),plinko_path("s","c",1,12))
class ApiTests(TestCase):
 def setUp(self):self.c=APIClient();self.c.get("/api/seeds/current/")
 def test_dice_idempotency(self):
  h={"HTTP_IDEMPOTENCY_KEY":"same-key"}
  a=self.c.post("/api/games/dice/play/",{"stake":"10","target":50},format="json",**h)
  b=self.c.post("/api/games/dice/play/",{"stake":"10","target":50},format="json",**h)
  self.assertEqual(a.status_code,201);self.assertEqual(a.data["id"],b.data["id"]);self.assertEqual(GameRound.objects.count(),1)
 def test_insufficient_balance(self):
  Wallet.objects.filter(owner_key="demo-user").update(balance=Decimal("0"))
  r=self.c.post("/api/games/dice/play/",{"stake":"10","target":50},format="json",HTTP_IDEMPOTENCY_KEY="poor")
  self.assertEqual(r.status_code,400)
 def test_plinko(self):
  r=self.c.post("/api/games/plinko/play/",{"stake":"1","rows":12,"risk":"medium"},format="json",HTTP_IDEMPOTENCY_KEY="p1")
  self.assertEqual(r.status_code,201,r.data);self.assertEqual(len(r.data["outcome"]["path"]),12)
 def test_rotation_reveals(self):
  r=self.c.post("/api/seeds/rotate/",{},format="json")
  self.assertEqual(r.status_code,200);self.assertEqual(commitment(r.data["retired"]["server_seed"]),r.data["retired"]["commitment"])
