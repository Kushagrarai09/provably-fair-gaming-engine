from decimal import Decimal,ROUND_DOWN
from django.db import transaction,IntegrityError
from django.utils import timezone
from django.core.signing import dumps,loads
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SeedRotation,GameRound
from .serializers import *
from .fairness import *
from .ledger import apply_delta,wallet_snapshot,LedgerError
OWNER="demo-user"
def seal(seed): return dumps(seed,salt="fairgame-seed")
def unseal(value): return loads(value,salt="fairgame-seed")
def active_seed():
 s=SeedRotation.objects.filter(status="active").first()
 if s:return s
 raw=new_server_seed()
 return SeedRotation.objects.create(server_seed_encrypted=seal(raw),server_seed_hash=commitment(raw),client_seed="demo-client-seed")
def payload(r,replayed=False):
 return {"id":r.id,"game_type":r.game_type,"nonce":r.nonce,"rules_version":r.rules_version,"client_seed":r.client_seed_snapshot,"commitment":r.commitment_snapshot,"outcome":r.outcome,"stake":str(r.stake),"payout":str(r.payout),"profit":str(r.profit),"status":r.status,"ledger_reference":r.ledger_reference,"created_at":r.created_at,"replayed":replayed}
@api_view(["GET"])
def health(request): return Response({"ok":True,"service":"provably-fair-gaming-engine","mode":"virtual-credits"})
@api_view(["GET"])
def wallet(request):
 w=wallet_snapshot(OWNER)
 from .models import LedgerEntry
 return Response({"owner":w.owner_key,"balance":str(w.balance),"currency":"VC","ledger_entries":LedgerEntry.objects.filter(owner_key=OWNER).count()})
@api_view(["GET"])
def current_seed(request):
 s=active_seed()
 return Response({"commitment":s.server_seed_hash,"client_seed":s.client_seed,"next_nonce":s.next_nonce,"status":s.status,"created_at":s.created_at})
@api_view(["POST"])
def set_client_seed(request):
 ser=ClientSeedSerializer(data=request.data);ser.is_valid(raise_exception=True)
 with transaction.atomic():
  s=SeedRotation.objects.select_for_update().filter(status="active").first() or active_seed()
  s.client_seed=ser.validated_data["client_seed"];s.save(update_fields=["client_seed"])
 return Response({"commitment":s.server_seed_hash,"client_seed":s.client_seed,"next_nonce":s.next_nonce})
@api_view(["POST"])
def rotate_seed(request):
 with transaction.atomic():
  s=SeedRotation.objects.select_for_update().filter(status="active").first() or active_seed()
  if s.rounds.filter(status="pending").exists():return Response({"error":"Cannot rotate with unsettled rounds."},status=409)
  raw=unseal(s.server_seed_encrypted);s.status="retired";s.revealed_seed=raw;s.revealed_at=timezone.now();s.save()
  new=new_server_seed()
  n=SeedRotation.objects.create(server_seed_encrypted=seal(new),server_seed_hash=commitment(new),client_seed=s.client_seed)
 return Response({"retired":{"commitment":s.server_seed_hash,"server_seed":raw,"revealed_at":s.revealed_at},"active":{"commitment":n.server_seed_hash,"client_seed":n.client_seed,"next_nonce":n.next_nonce}})
def play(request,game,serializer):
 ser=serializer(data=request.data);ser.is_valid(raise_exception=True);d=ser.validated_data
 key=request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
 if not key or len(key)>128:return Response({"error":"A unique Idempotency-Key header is required."},status=400)
 old=GameRound.objects.filter(idempotency_key=key).first()
 if old:return Response(payload(old,True))
 try:
  with transaction.atomic():
   s=SeedRotation.objects.select_for_update().filter(status="active").first() or active_seed()
   nonce=s.next_nonce;s.next_nonce+=1;s.save(update_fields=["next_nonce"])
   server=unseal(s.server_seed_encrypted);stake=d["stake"]
   apply_delta(OWNER,-stake,key+":stake","stake",key)
   if game=="dice":
    raw=dice_result(server,s.client_seed,nonce);target=d["target"];won=raw<target*100
    payout=(stake*Decimal("99")/Decimal(target)).quantize(Decimal(".01"),rounding=ROUND_DOWN) if won else Decimal("0")
    out={"result":f"{raw/100:.2f}","result_basis_points":raw,"target":target,"won":won,"win_chance_percent":target,"multiplier":str(Decimal("99")/Decimal(target))}
   elif game=="crash":
    cp=crash_multiplier_x100(server,s.client_seed,nonce);target=int(d["cashout_at"]*100);won=cp>=target
    payout=(stake*Decimal(target)/100*Decimal(".99")).quantize(Decimal(".01"),rounding=ROUND_DOWN) if won else Decimal("0")
    out={"crash_multiplier":f"{cp/100:.2f}","cashout_at":str(d["cashout_at"]),"won":won}
   else:
    path=plinko_path(server,s.client_seed,nonce,d["rows"]);slot=sum(path);risk=d["risk"]
    tables={"low":[.7,.8,.9,1,1.1,1.2,1.4,1.6,2],"medium":[.3,.5,.8,1,1.5,2,3,5,10],"high":[0,.2,.5,1,2,5,10,25,50]}
    mult=Decimal(str(tables[risk][min(8,round(abs(slot-d["rows"]/2)))]))
    payout=(stake*mult).quantize(Decimal(".01"),rounding=ROUND_DOWN)
    out={"rows":d["rows"],"risk":risk,"path":path,"slot":slot,"multiplier":str(mult),"won":payout>stake}
   apply_delta(OWNER,payout,key+":payout","payout",key)
   r=GameRound.objects.create(seed_rotation=s,nonce=nonce,game_type=game,rules_version="demo-v1",client_seed_snapshot=s.client_seed,commitment_snapshot=s.server_seed_hash,outcome=out,stake=stake,payout=payout,profit=payout-stake,idempotency_key=key,status="settled",ledger_reference=key,settled_at=timezone.now())
 except LedgerError as e:return Response({"error":str(e)},status=400)
 except IntegrityError:
  r=GameRound.objects.filter(idempotency_key=key).first()
  if r:return Response(payload(r,True))
  return Response({"error":"Concurrent request conflict. Retry with the same key."},status=409)
 return Response(payload(r),status=201)
@api_view(["POST"])
def dice_play(request):return play(request,"dice",DicePlaySerializer)
@api_view(["POST"])
def crash_play(request):return play(request,"crash",CrashPlaySerializer)
@api_view(["POST"])
def plinko_play(request):return play(request,"plinko",PlinkoPlaySerializer)
@api_view(["GET"])
def history(request):return Response([payload(r) for r in GameRound.objects.all()[:100]])
@api_view(["GET"])
def round_detail(request,round_id):
 try:r=GameRound.objects.get(pk=round_id)
 except GameRound.DoesNotExist:return Response({"error":"Round not found"},status=404)
 d=payload(r)
 if r.seed_rotation.status=="retired":d["server_seed"]=r.seed_rotation.revealed_seed
 return Response(d)
@api_view(["POST"])
def verify_round(request):
 ser=VerifySerializer(data=request.data);ser.is_valid(raise_exception=True);d=ser.validated_data
 try:r=verify(d["server_seed"],d["commitment"],d["client_seed"],d["nonce"],d["game_type"],d.get("expected_outcome"))
 except ValueError as e:return Response({"error":str(e)},status=400)
 return Response(r)
