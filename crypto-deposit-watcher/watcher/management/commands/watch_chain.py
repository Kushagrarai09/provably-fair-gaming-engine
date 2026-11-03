import logging, time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from watcher.models import DepositAddress, Deposit, BlockCheckpoint
from watcher.services import web3_client, env_int, credit_deposit

logger = logging.getLogger("watcher.chain")
class Command(BaseCommand):
    help = "Scan Ethereum Sepolia blocks for incoming native ETH transactions."
    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--from-block", type=int, default=None)
    def handle(self, *args, **opts):
        while True:
            try:
                w3 = web3_client()
                self.scan_pass(w3, opts.get("from_block"))
                if opts["once"]: return
                time.sleep(max(2, env_int("SCAN_INTERVAL_SECONDS", 8)))
            except KeyboardInterrupt: return
            except Exception:
                logger.exception("watcher pass failed")
                if opts["once"]: raise
                time.sleep(max(5, env_int("SCAN_INTERVAL_SECONDS", 8)))
    def scan_pass(self, w3, override_from=None):
        chain_id, latest = w3.eth.chain_id, w3.eth.block_number
        threshold = max(1, env_int("CONFIRMATIONS_REQUIRED", 12))
        last = BlockCheckpoint.objects.order_by("-block_number").first()
        if override_from is not None: start = override_from
        elif last:
            # Re-check persisted tip after restart in case it was reorganized while offline.
            canonical = w3.eth.get_block(last.block_number)
            if canonical["hash"].hex().lower() != last.block_hash.lower():
                self.handle_reorg(w3, last.block_number)
                start = last.block_number
            else: start = last.block_number + 1
        else: start = env_int("START_BLOCK", 0)
        tracked = {a.address.lower(): a for a in DepositAddress.objects.filter(is_active=True)}
        for number in range(start, latest + 1):
            block = w3.eth.get_block(number, full_transactions=True)
            block_hash, parent_hash = block["hash"].hex(), block["parentHash"].hex()
            previous = BlockCheckpoint.objects.filter(block_number=number-1).first()
            if previous and previous.block_hash.lower() != parent_hash.lower():
                self.handle_reorg(w3, number-1)
            with transaction.atomic():
                BlockCheckpoint.objects.update_or_create(block_number=number, defaults={
                    "chain_id": chain_id, "block_hash": block_hash, "parent_hash": parent_hash})
                for tx in block["transactions"]:
                    to_addr = tx.get("to")
                    if not to_addr or to_addr.lower() not in tracked or int(tx["value"]) <= 0: continue
                    receipt = w3.eth.get_transaction_receipt(tx["hash"])
                    if int(receipt["status"]) != 1: continue
                    tx_hash = tx["hash"].hex()
                    Deposit.objects.get_or_create(chain_id=chain_id, tx_hash=tx_hash, log_index=0, defaults={
                        "address": tracked[to_addr.lower()], "from_address": tx["from"], "to_address": to_addr,
                        "amount_wei": Decimal(int(tx["value"])), "block_number": number,
                        "block_hash": block_hash, "status": Deposit.Status.DETECTED})
        self.update_deposits(w3, latest, threshold)
        logger.info("scan complete blocks=%s..%s latest=%s", start, latest, latest)
    def update_deposits(self, w3, latest, threshold):
        for dep in Deposit.objects.exclude(status__in=[Deposit.Status.CREDITED, Deposit.Status.REORGED, Deposit.Status.FAILED]):
            try:
                canonical = w3.eth.get_block(dep.block_number)
                receipt = w3.eth.get_transaction_receipt(dep.tx_hash)
                if canonical["hash"].hex().lower() != dep.block_hash.lower() or int(receipt["status"]) != 1 or receipt["blockHash"].hex().lower() != dep.block_hash.lower():
                    dep.status, dep.error = Deposit.Status.REORGED, "Stored block/receipt no longer matches canonical chain"
                    dep.save(update_fields=["status", "error"]); continue
                dep.confirmations = max(0, latest - dep.block_number + 1)
                dep.status = Deposit.Status.CONFIRMED if dep.confirmations >= threshold else Deposit.Status.CONFIRMING
                dep.save(update_fields=["confirmations", "status"])
                if dep.status == Deposit.Status.CONFIRMED: credit_deposit(dep.pk)
            except Exception as exc:
                dep.error = str(exc)[:2000]; dep.save(update_fields=["error"])
                logger.exception("deposit update failed tx=%s", dep.tx_hash)
    def handle_reorg(self, w3, changed_number):
        for dep in Deposit.objects.filter(block_number__gte=changed_number).exclude(status=Deposit.Status.REORGED):
            if w3.eth.get_block(dep.block_number)["hash"].hex().lower() != dep.block_hash.lower():
                if dep.status == Deposit.Status.CREDITED:
                    logger.critical("credited deposit requires manual reconciliation tx=%s", dep.tx_hash)
                    dep.error = "Credited deposit affected by reorg; manual reconciliation required"
                else:
                    dep.status, dep.error = Deposit.Status.REORGED, "Block reorganized before credit"
                dep.save(update_fields=["status", "error"])
        BlockCheckpoint.objects.filter(block_number__gte=changed_number).delete()
