"""
REST API endpoints for Anchor management.

Provides HTTP endpoints for:
- GET /v1/anchors - Get all anchor states
- PATCH /v1/anchors/{slot} - Update specific anchor slot
"""

from typing import Dict, Any, Optional
from pathlib import Path
import time
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Path as FastAPIPath
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create placeholder classes for type hints
    class BaseModel:
        pass
    class Field:
        def __init__(self, *args, **kwargs):
            pass


class AnchorState(BaseModel):
    """Anchor state response model"""
    slot: str
    anchor_block_id: str
    hop_budget: int
    pinned: bool
    last_used_ts: int
    summary: str


class AnchorsResponse(BaseModel):
    """Full anchors response model"""
    version: int
    slots: list[AnchorState]
    updated_at: int


class AnchorUpdateRequest(BaseModel):
    """Anchor update request model"""
    anchor_block_id: Optional[str] = Field(None, description="New anchor block ID")
    hop_budget: Optional[int] = Field(None, ge=1, le=3, description="Hop budget (1-3)")
    pinned: Optional[bool] = Field(None, description="Pin/unpin anchor")


# FastAPI app instance (to be imported by main API server)
anchors_router = None

if FASTAPI_AVAILABLE:
    try:
        from fastapi import APIRouter
        anchors_router = APIRouter(prefix="/v1/anchors", tags=["anchors"])
    except ImportError:
        anchors_router = None
else:
    anchors_router = None

if FASTAPI_AVAILABLE and anchors_router is not None:

    @anchors_router.get("", response_model=AnchorsResponse)
    async def get_anchors():
        """Get current anchor states for all slots"""
        try:
            from ..anchors import AnchorManager
            
            anchor_path = Path("data/anchors.json")
            if not anchor_path.exists():
                raise HTTPException(
                    status_code=404, 
                    detail="Anchor system not initialized. Run bootstrap first."
                )
            
            anchor_manager = AnchorManager(anchor_path)
            
            # Get all slot info
            slots = []
            for slot_name in ['A', 'B', 'C']:
                slot_info = anchor_manager.get_slot_info(slot_name)
                if slot_info:
                    slots.append(AnchorState(
                        slot=slot_info['slot'],
                        anchor_block_id=slot_info['anchor_block_id'],
                        hop_budget=slot_info['hop_budget'],
                        pinned=slot_info['pinned'],
                        last_used_ts=slot_info['last_used_ts'],
                        summary=slot_info['summary']
                    ))
            
            # Get metadata from anchor manager
            anchor_data = anchor_manager._load_state()
            
            return AnchorsResponse(
                version=anchor_data.get('version', 1),
                slots=slots,
                updated_at=anchor_data.get('updated_at', int(time.time()))
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get anchors: {str(e)}")

    @anchors_router.patch("/{slot}", response_model=AnchorState)
    async def update_anchor(
        slot: str = FastAPIPath(..., regex="^[ABC]$", description="Anchor slot (A, B, or C)"),
        update_data: AnchorUpdateRequest = ...
    ):
        """Update specific anchor slot configuration"""
        try:
            from ..anchors import AnchorManager
            from ..core import BlockManager, DatabaseManager
            import numpy as np
            
            # Load anchor manager
            anchor_path = Path("data/anchors.json")
            if not anchor_path.exists():
                raise HTTPException(
                    status_code=404, 
                    detail="Anchor system not initialized. Run bootstrap first."
                )
            
            anchor_manager = AnchorManager(anchor_path)
            
            # Check if slot exists
            current_info = anchor_manager.get_slot_info(slot)
            if not current_info:
                raise HTTPException(status_code=404, detail=f"Slot {slot} not found")
            
            # Validate and update anchor block if requested
            if update_data.anchor_block_id is not None:
                # Validate block exists
                db_manager = DatabaseManager()
                block_manager = BlockManager(db_manager)
                
                try:
                    block_data = block_manager.db_manager.get_block_by_index(int(update_data.anchor_block_id))
                    if not block_data:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Block #{update_data.anchor_block_id} does not exist"
                        )
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid block ID: {update_data.anchor_block_id}"
                    )
                
                # Move anchor to new block
                block_embedding = np.array(block_data.get('embedding', [0.0] * 128))
                anchor_manager.move_anchor(slot, update_data.anchor_block_id, block_embedding)
            
            # Update hop budget if requested
            if update_data.hop_budget is not None:
                anchor_manager.set_hop_budget(slot, update_data.hop_budget)
            
            # Update pin status if requested
            if update_data.pinned is not None:
                if update_data.pinned:
                    anchor_manager.pin_anchor(slot)
                else:
                    anchor_manager.unpin_anchor(slot)
            
            # Return updated state
            updated_info = anchor_manager.get_slot_info(slot)
            return AnchorState(
                slot=updated_info['slot'],
                anchor_block_id=updated_info['anchor_block_id'],
                hop_budget=updated_info['hop_budget'],
                pinned=updated_info['pinned'],
                last_used_ts=updated_info['last_used_ts'],
                summary=updated_info['summary']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update anchor: {str(e)}")

else:
    # Fallback for when FastAPI is not available
    def create_flask_routes():
        """Create Flask routes as fallback"""
        try:
            from flask import Flask, jsonify, request
            FLASK_AVAILABLE = True
        except ImportError:
            FLASK_AVAILABLE = False
        
        def register_anchor_routes(app=None):
            """Register anchor routes with Flask app (if available)"""
            if not FLASK_AVAILABLE or app is None:
                return lambda app: None  # Return no-op function
            
            @app.route('/v1/anchors', methods=['GET'])
            def get_anchors():
                """Get current anchor states for all slots"""
                try:
                    from ..anchors import AnchorManager
                    
                    anchor_path = Path("data/anchors.json")
                    if not anchor_path.exists():
                        return jsonify({
                            "error": "Anchor system not initialized. Run bootstrap first."
                        }), 404
                    
                    anchor_manager = AnchorManager(anchor_path)
                    
                    # Get all slot info
                    slots = []
                    for slot_name in ['A', 'B', 'C']:
                        slot_info = anchor_manager.get_slot_info(slot_name)
                        if slot_info:
                            slots.append({
                                'slot': slot_info['slot'],
                                'anchor_block_id': slot_info['anchor_block_id'],
                                'hop_budget': slot_info['hop_budget'],
                                'pinned': slot_info['pinned'],
                                'last_used_ts': slot_info['last_used_ts'],
                                'summary': slot_info['summary']
                            })
                    
                    # Get metadata
                    anchor_data = anchor_manager._load_state()
                    
                    return jsonify({
                        'version': anchor_data.get('version', 1),
                        'slots': slots,
                        'updated_at': anchor_data.get('updated_at', int(time.time()))
                    })
                    
                except Exception as e:
                    return jsonify({"error": f"Failed to get anchors: {str(e)}"}), 500
            
            @app.route('/v1/anchors/<slot>', methods=['PATCH'])
            def update_anchor(slot):
                """Update specific anchor slot configuration"""
                if slot not in ['A', 'B', 'C']:
                    return jsonify({"error": f"Invalid slot: {slot}. Must be A, B, or C"}), 400
                
                try:
                    from ..anchors import AnchorManager
                    from ..core import BlockManager, DatabaseManager
                    import numpy as np
                    
                    update_data = request.get_json() or {}
                    
                    # Load anchor manager
                    anchor_path = Path("data/anchors.json")
                    if not anchor_path.exists():
                        return jsonify({
                            "error": "Anchor system not initialized. Run bootstrap first."
                        }), 404
                    
                    anchor_manager = AnchorManager(anchor_path)
                    
                    # Check if slot exists
                    current_info = anchor_manager.get_slot_info(slot)
                    if not current_info:
                        return jsonify({"error": f"Slot {slot} not found"}), 404
                    
                    # Update anchor block if requested
                    if 'anchor_block_id' in update_data:
                        block_id = update_data['anchor_block_id']
                        
                        # Validate block exists
                        db_manager = DatabaseManager()
                        block_manager = BlockManager(db_manager)
                        
                        try:
                            block_data = block_manager.db_manager.get_block_by_index(int(block_id))
                            if not block_data:
                                return jsonify({
                                    "error": f"Block #{block_id} does not exist"
                                }), 400
                        except ValueError:
                            return jsonify({"error": f"Invalid block ID: {block_id}"}), 400
                        
                        # Move anchor
                        block_embedding = np.array(block_data.get('embedding', [0.0] * 128))
                        anchor_manager.move_anchor(slot, block_id, block_embedding)
                    
                    # Update hop budget if requested
                    if 'hop_budget' in update_data:
                        hop_budget = update_data['hop_budget']
                        if not isinstance(hop_budget, int) or not (1 <= hop_budget <= 3):
                            return jsonify({"error": "hop_budget must be integer between 1-3"}), 400
                        anchor_manager.set_hop_budget(slot, hop_budget)
                    
                    # Update pin status if requested
                    if 'pinned' in update_data:
                        pinned = update_data['pinned']
                        if not isinstance(pinned, bool):
                            return jsonify({"error": "pinned must be boolean"}), 400
                        
                        if pinned:
                            anchor_manager.pin_anchor(slot)
                        else:
                            anchor_manager.unpin_anchor(slot)
                    
                    # Return updated state
                    updated_info = anchor_manager.get_slot_info(slot)
                    return jsonify({
                        'slot': updated_info['slot'],
                        'anchor_block_id': updated_info['anchor_block_id'],
                        'hop_budget': updated_info['hop_budget'],
                        'pinned': updated_info['pinned'],
                        'last_used_ts': updated_info['last_used_ts'],
                        'summary': updated_info['summary']
                    })
                    
                except Exception as e:
                    return jsonify({"error": f"Failed to update anchor: {str(e)}"}), 500
            
            return register_anchor_routes
    
    # Export Flask route registration function
    try:
        register_anchor_routes = create_flask_routes()
    except ImportError:
        # Ultimate fallback - just provide the function signature
        def register_anchor_routes():
            """Placeholder for when no web framework is available"""
            return lambda app: None


# Utility functions for integration
def get_anchor_api_info() -> Dict[str, Any]:
    """Get API endpoint information for documentation"""
    return {
        "endpoints": [
            {
                "path": "/v1/anchors",
                "method": "GET",
                "description": "Get all anchor states",
                "response_model": "AnchorsResponse"
            },
            {
                "path": "/v1/anchors/{slot}",
                "method": "PATCH", 
                "description": "Update specific anchor slot",
                "parameters": ["slot: A|B|C"],
                "request_model": "AnchorUpdateRequest",
                "response_model": "AnchorState"
            }
        ],
        "models": {
            "AnchorState": {
                "slot": "str",
                "anchor_block_id": "str", 
                "hop_budget": "int (1-3)",
                "pinned": "bool",
                "last_used_ts": "int (timestamp)",
                "summary": "str"
            },
            "AnchorsResponse": {
                "version": "int",
                "slots": "list[AnchorState]",
                "updated_at": "int (timestamp)"
            },
            "AnchorUpdateRequest": {
                "anchor_block_id": "str (optional)",
                "hop_budget": "int 1-3 (optional)",
                "pinned": "bool (optional)"
            }
        }
    }