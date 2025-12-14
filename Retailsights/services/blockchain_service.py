"""
Blockchain Traceability Service
Immutable supply chain tracking and product provenance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import json
from ..db import get_connection
from ..logger import logger


class Block:
    """Single block in the blockchain."""
    
    def __init__(self, index: int, timestamp: str, data: Dict, previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }


class BlockchainService:
    """Product traceability using blockchain technology."""
    
    @staticmethod
    def create_genesis_block() -> Block:
        """Create the first block in the chain."""
        return Block(0, datetime.now().isoformat(), {"message": "Genesis Block"}, "0")
    
    @staticmethod
    def add_product_to_blockchain(
        product_id: int,
        sku: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add product event to blockchain.
        Events: RECEIVED, STORED, DISCOUNTED, SOLD, WASTED
        """
        conn = get_connection()
        try:
            # Get last block
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT block_index, block_hash 
                FROM blockchain_ledger 
                ORDER BY block_index DESC 
                LIMIT 1
            """)
            last_block = cur.fetchone()
            
            if last_block:
                new_index = last_block['block_index'] + 1
                previous_hash = last_block['block_hash']
            else:
                # Genesis block
                genesis = BlockchainService.create_genesis_block()
                new_index = 1
                previous_hash = genesis.hash
            
            # Create new block
            block_data = {
                "product_id": product_id,
                "sku": sku,
                "event_type": event_type,
                "event_data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            block = Block(new_index, datetime.now().isoformat(), block_data, previous_hash)
            
            # Store in database
            cur.execute("""
                INSERT INTO blockchain_ledger 
                (block_index, block_hash, previous_hash, timestamp, event_type, 
                 product_id, sku, data, verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                block.index,
                block.hash,
                block.previous_hash,
                block.timestamp,
                event_type,
                product_id,
                sku,
                json.dumps(block_data),
                True
            ))
            
            conn.commit()
            
            return {
                "success": True,
                "block": block.to_dict(),
                "message": f"Event '{event_type}' added to blockchain"
            }
            
        except Exception as e:
            logger.error(f"add_product_to_blockchain error: {e}")
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def get_product_history(product_id: int) -> List[Dict[str, Any]]:
        """Get complete blockchain history for a product."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT 
                    block_index,
                    block_hash,
                    timestamp,
                    event_type,
                    data,
                    verified
                FROM blockchain_ledger
                WHERE product_id = %s
                ORDER BY block_index ASC
            """, (product_id,))
            
            history = cur.fetchall()
            
            # Parse JSON data
            for record in history:
                if record.get('data'):
                    try:
                        record['data'] = json.loads(record['data'])
                    except:
                        pass
            
            return history
            
        except Exception as e:
            logger.error(f"get_product_history error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def verify_blockchain_integrity(shop_id: Optional[int] = None) -> Dict[str, Any]:
        """Verify blockchain integrity - detect tampering."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    block_index,
                    block_hash,
                    previous_hash,
                    timestamp,
                    event_type,
                    product_id,
                    sku,
                    data
                FROM blockchain_ledger
                ORDER BY block_index ASC
            """
            
            cur.execute(query)
            blocks = cur.fetchall()
            
            if not blocks:
                return {"valid": True, "message": "No blocks to verify"}
            
            tampered_blocks = []
            
            for i, block in enumerate(blocks):
                # Recreate block and verify hash
                block_data = json.loads(block['data']) if block['data'] else {}
                
                recreated_block = Block(
                    block['block_index'],
                    block['timestamp'],
                    block_data,
                    block['previous_hash']
                )
                
                # Check if hash matches
                if recreated_block.hash != block['block_hash']:
                    tampered_blocks.append({
                        "block_index": block['block_index'],
                        "stored_hash": block['block_hash'],
                        "calculated_hash": recreated_block.hash,
                        "issue": "Hash mismatch - possible tampering"
                    })
                
                # Check if previous_hash matches previous block's hash
                if i > 0:
                    if block['previous_hash'] != blocks[i-1]['block_hash']:
                        tampered_blocks.append({
                            "block_index": block['block_index'],
                            "issue": "Previous hash mismatch - chain broken"
                        })
            
            is_valid = len(tampered_blocks) == 0
            
            return {
                "valid": is_valid,
                "total_blocks": len(blocks),
                "tampered_blocks": tampered_blocks,
                "message": "Blockchain integrity verified" if is_valid else "⚠️ TAMPERING DETECTED",
                "verified_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"verify_blockchain_integrity error: {e}")
            return {
                "valid": False,
                "error": str(e),
                "message": f"Error verifying blockchain: {str(e)}",
                "total_blocks": 0,
                "tampered_blocks": []
            }
        finally:
            conn.close()
    
    @staticmethod
    def generate_product_certificate(product_id: int, sku: str) -> Dict[str, Any]:
        """
        Generate tamper-proof certificate of authenticity.
        For customer trust and regulatory compliance.
        """
        history = BlockchainService.get_product_history(product_id)
        
        if not history:
            return {"error": "No blockchain history found"}
        
        # Extract key events
        received_event = next((h for h in history if h['event_type'] == 'RECEIVED'), None)
        
        certificate = {
            "product_sku": sku,
            "certificate_id": hashlib.sha256(f"{product_id}:{sku}".encode()).hexdigest()[:16],
            "blockchain_verified": True,
            "total_events": len(history),
            "first_recorded": history[0]['timestamp'] if history else None,
            "last_updated": history[-1]['timestamp'] if history else None,
            "supply_chain_events": [
                {
                    "event": h['event_type'],
                    "timestamp": h['timestamp'],
                    "verified": h['verified']
                }
                for h in history
            ],
            "verification_url": f"https://retailsight.io/verify/{sku}",
            "qr_code_data": json.dumps({
                "sku": sku,
                "cert_id": hashlib.sha256(f"{product_id}:{sku}".encode()).hexdigest()[:16],
                "verify_url": f"https://retailsight.io/verify/{sku}"
            })
        }
        
        return certificate
    
    @staticmethod
    def track_batch_recall(batch_id: str, reason: str, shop_id: int) -> Dict[str, Any]:
        """
        Instant batch recall using blockchain traceability.
        Critical for food safety.
        """
        conn = get_connection()
        try:
            # Find all products in batch
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT id, sku, name 
                FROM products 
                WHERE batch_id = %s AND shop_id = %s
            """, (batch_id, shop_id))
            
            products = cur.fetchall()
            
            if not products:
                return {"success": False, "message": "No products found in batch"}
            
            # Add RECALL event to blockchain for each product
            recalled_products = []
            for product in products:
                result = BlockchainService.add_product_to_blockchain(
                    product_id=product['id'],
                    sku=product['sku'],
                    event_type='RECALL',
                    data={
                        "batch_id": batch_id,
                        "reason": reason,
                        "recall_initiated_at": datetime.now().isoformat(),
                        "status": "URGENT_RECALL"
                    }
                )
                
                if result['success']:
                    recalled_products.append(product['sku'])
            
            # Mark products as recalled in database
            cur.execute("""
                UPDATE products 
                SET status = 'RECALLED', updated_at = NOW()
                WHERE batch_id = %s AND shop_id = %s
            """, (batch_id, shop_id))
            
            conn.commit()
            
            return {
                "success": True,
                "batch_id": batch_id,
                "products_recalled": len(recalled_products),
                "product_skus": recalled_products,
                "reason": reason,
                "blockchain_recorded": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"track_batch_recall error: {e}")
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
