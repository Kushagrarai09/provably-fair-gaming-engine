import hashlib,hmac,secrets
def new_server_seed(): return secrets.token_hex(32)
def commitment(seed): return hashlib.sha256(seed.encode("utf-8")).hexdigest()
def digest(seed,client,nonce):
 return hmac.new(seed.encode("utf-8"),f"{client}:{nonce}".encode("utf-8"),hashlib.sha256).digest()
def dice_result(seed,client,nonce): return int.from_bytes(digest(seed,client,nonce)[:4],"big")*10000//(2**32)
def crash_multiplier_x100(seed,client,nonce,edge_bps=100):
 raw=int.from_bytes(digest(seed,client,nonce)[:7],"big")>>4
 if raw==0: return 100
 scale=2**52
 return max(100,min(100000,((10000-edge_bps)*scale)//((scale-raw)*100)))
def plinko_path(seed,client,nonce,rows):
 if not 8<=rows<=16: raise ValueError("rows must be 8..16")
 out=[]; counter=0
 while len(out)<rows:
  block=digest(seed,client,nonce) if counter==0 else hmac.new(seed.encode(),f"{client}:{nonce}:{counter}".encode(),hashlib.sha256).digest()
  for byte in block:
   for bit in range(7,-1,-1):
    out.append((byte>>bit)&1)
    if len(out)==rows: return out
  counter+=1
 return out
def verify(seed,expected_hash,client,nonce,game_type,expected_outcome=None):
 actual=commitment(seed); hash_ok=hmac.compare_digest(actual,expected_hash)
 if game_type=="dice": outcome=dice_result(seed,client,nonce)
 elif game_type=="crash": outcome=crash_multiplier_x100(seed,client,nonce)
 elif game_type=="plinko": outcome=plinko_path(seed,client,nonce,12)
 else: raise ValueError("Unsupported game type")
 outcome_ok=expected_outcome is None or str(outcome)==str(expected_outcome)
 return {"valid":hash_ok and outcome_ok,"commitment_valid":hash_ok,"outcome_valid":outcome_ok,"commitment":actual,"outcome":outcome}
