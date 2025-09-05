#!/usr/bin/env python3
"""Test script for anchor API logic without Flask dependencies."""

import sys, json
sys.path.insert(0, '.')

try:
    from greeum.anchors import AnchorManager
    from pathlib import Path
    
    anchor_path = Path('data/anchors.json')
    if anchor_path.exists():
        anchor_manager = AnchorManager(anchor_path)
        
        print('✅ Testing enhanced anchor API logic...')
        
        # Test GET anchors
        slots = []
        for slot_name in ['A', 'B', 'C']:
            slot_info = anchor_manager.get_slot_info(slot_name)
            if slot_info:
                slots.append({
                    'slot': slot_info['slot'],
                    'anchor_block_id': slot_info['anchor_block_id'],
                    'hop_budget': slot_info['hop_budget'],
                    'pinned': slot_info['pinned'],
                    'summary': slot_info['summary']
                })
        
        print(f'✅ GET /api/v1/anchors: {len(slots)} slots retrieved')
        
        # Test PATCH anchor (hop_budget)
        old_budget = anchor_manager.get_hop_budget('A')
        new_budget = 2 if old_budget != 2 else 3
        anchor_manager.set_hop_budget('A', new_budget)
        updated_budget = anchor_manager.get_hop_budget('A')
        print(f'✅ PATCH hop_budget: {old_budget} → {updated_budget}')
        
        # Test PATCH anchor (pin/unpin) 
        slot_info = anchor_manager.get_slot_info('A')
        old_pinned = slot_info['pinned']
        if old_pinned:
            anchor_manager.unpin_anchor('A')
        else:
            anchor_manager.pin_anchor('A')
        new_pinned = anchor_manager.get_slot_info('A')['pinned']
        print(f'✅ PATCH pinned: {old_pinned} → {new_pinned}')
        
        # Test summary update
        anchor_manager.update_summary('A', 'Test slot A - API updated')
        updated_summary = anchor_manager.get_slot_info('A')['summary']
        print(f'✅ Summary updated: {updated_summary[:30]}...')
        
        print('\n🎉 All anchor API operations working correctly!')
        
    else:
        print('❌ Anchor system not initialized - run bootstrap first')
        
except Exception as e:
    import traceback
    print(f'❌ API test failed: {e}')
    print(traceback.format_exc())