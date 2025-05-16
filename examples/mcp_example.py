import os
import sys
import argparse
import json

# MemoryEngine uc784ud3ecud2b8ub97c uc704ud55c uacbdub85c ucd94uac00
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MCP ub9acub2c8 ud074ub77cuad6duc5d0uc11c uc784ud3ecud2b8
from memory_engine.mcp_client import MCPClient
from memory_engine.mcp_service import MCPService
from memory_engine.mcp_integrations import MCPIntegrations

def run_mcp_server(data_dir="./data", port=8000):
    """
    MCP uc11cube44uc2a4ub97c uc2e4ud589ud569ub2c8ub2e4.
    
    Args:
        data_dir: ub370uc774ud130 ub514ub809ud1a0ub9ac
        port: uc11cube44uc2a4 ud3ecud2b8
    """
    service = MCPService(data_dir=data_dir, port=port)
    print(f"MCP uc11cube44uc2a4 uc2dcuc791: http://localhost:{port}")
    service.start()

def create_api_key():
    """
    MCP uc11cube44uc2a4uc5d0 uc0c8 API ud0a4ub97c uc0dduc131ud569ub2c8ub2e4.
    """
    import requests
    import json
    
    # uad00ub9acuc790 ud0a4ub294 ud658uacbd ubcc0uc218 ub610ub294 uad6cuac00ud558uc5ec uc124uc815
    admin_key = os.environ.get("ADMIN_KEY", "admin_secret")
    
    # API ud0a4 uc0dduc131 uc694uccad
    response = requests.post(
        "http://localhost:8000/api/mcp/admin/api_key",
        json={"action": "create", "admin_key": admin_key, "name": "Example API Key"}
    )
    
    if response.status_code == 200:
        data = response.json()
        api_key = data.get("api_key")
        print(f"uc0c8 API ud0a4 uc0dduc131: {api_key}")
        return api_key
    else:
        print(f"API ud0a4 uc0dduc131 uc2e4ud328: {response.text}")
        return None

def test_memory_operations(api_key):
    """
    MCP ud074ub77cuad6duc5d0uc11c uae30uc5b5 uc791uc5c5 ud14cuc2a4ud2b8
    
    Args:
        api_key: MCP API ud0a4
    """
    client = MCPClient(api_key=api_key)
    
    # uae30uc5b5 ucd94uac00
    print("\n=== uae30uc5b5 ucd94uac00 ud14cuc2a4ud2b8 ===")
    memory_result = client.manage_memory(
        action="add",
        memory_content="MCP ud14cuc2a4ud2b8 uae30uc5b5uc785ub2c8ub2e4. uc774 uae30uc5b5uc740 MCP ud074ub77cuad6duck640 MemoryEngine uc5f0ub3d9 ud14cuc2a4ud2b8ub97c uc704ud574 uc0dduc131ub418uc5c8uc2b5ub2c8ub2e4."
    )
    
    if "memory_id" in memory_result:
        memory_id = memory_result["memory_id"]
        print(f"uae30uc5b5 ucd94uac00 uc131uacf5. ID: {memory_id}")
        
        # uae30uc5b5 uac00uc838uc624uae30
        print("\n=== uae30uc5b5 uac00uc838uc624uae30 ud14cuc2a4ud2b8 ===")
        get_result = client.manage_memory(action="get", memory_id=memory_id)
        if "memory" in get_result:
            print(f"uac00uc838uc628 uae30uc5b5: {get_result['memory']}")
        
        # uae30uc5b5 uac80uc0c9
        print("\n=== uae30uc5b5 uac80uc0c9 ud14cuc2a4ud2b8 ===")
        search_result = client.manage_memory(action="query", query="MCP ud14cuc2a4ud2b8", limit=5)
        if "results" in search_result:
            print(f"uac80uc0c9 uacb0uacfc: {len(search_result['results'])} uac1duc758 uae30uc5b5 ubc1cuacac")
            for i, mem in enumerate(search_result["results"]):
                print(f"  {i+1}. [{mem.get('id')}] {mem.get('content')}")
        
        # uae30uc5b5 uc5c5ub370uc774ud2b8
        print("\n=== uae30uc5b5 uc5c5ub370uc774ud2b8 ud14cuc2a4ud2b8 ===")
        update_result = client.manage_memory(
            action="update", 
            memory_id=memory_id,
            memory_content="uc5c5ub370uc774ud2b8ub41c MCP ud14cuc2a4ud2b8 uae30uc5b5uc785ub2c8ub2e4. uc774 uae30uc5b5uc740 uc131uacf5uc801uc73cub85c uc218uc815ub418uc5c8uc2b5ub2c8ub2e4."
        )
        if update_result.get("success"):
            print(f"uae30uc5b5 uc5c5ub370uc774ud2b8 uc131uacf5")
            
            # uc5c5ub370uc774ud2b8 ud655uc778
            get_updated = client.manage_memory(action="get", memory_id=memory_id)
            if "memory" in get_updated:
                print(f"uc5c5ub370uc774ud2b8ub41c uae30uc5b5: {get_updated['memory']}")
    else:
        print(f"uae30uc5b5 ucd94uac00 uc2e4ud328: {memory_result}")

def test_unity_integration(api_key):
    """
    Unity MCP uc5f0ub3d9 ud14cuc2a4ud2b8
    
    Args:
        api_key: MCP API ud0a4
    """
    client = MCPClient(api_key=api_key)
    
    print("\n=== Unity MCP uc5f0ub3d9 ud14cuc2a4ud2b8 ===")
    
    # Unity uba54ub274 uc544uc774ud15c uc2e4ud589 ud14cuc2a4ud2b8
    print("\n- Unity uba54ub274 uc544uc774ud15c uc2e4ud589 ud14cuc2a4ud2b8:")
    menu_result = client.execute_menu_item(menu_path="GameObject/Create Empty")
    print(f"  uacb0uacfc: {menu_result}")
    
    # Unity uac8cuc784uc624ube0cuc81dud2b8 uc120ud0dd ud14cuc2a4ud2b8
    print("\n- Unity uac8cuc784uc624ube0cuc81dud2b8 uc120ud0dd ud14cuc2a4ud2b8:")
    select_result = client.select_gameobject(object_path="Main Camera")
    print(f"  uacb0uacfc: {select_result}")
    
    # Unity ucf58uc194 ub85cuadf8 ud14cuc2a4ud2b8
    print("\n- Unity ucf58uc194 ub85cuadf8 ud14cuc2a4ud2b8:")
    log_result = client.send_console_log(message="MCP ud14cuc2a4ud2b8 ub85cuadf8 uba54uc2dcuc9c0", log_type="info")
    print(f"  uacb0uacfc: {log_result}")

def main():
    parser = argparse.ArgumentParser(description="Cursor MCP ud074ub77cuad6c uc0acuc6a9 uc608uc81c")
    parser.add_argument("--mode", choices=["server", "client"], default="client", help="uc11cube44uc2a4 ub610ub294 ud074ub77cuad6c ubaa8ub4dc uc120ud0dd")
    parser.add_argument("--data-dir", default="./data", help="ub370uc774ud130 ub514ub809ud1a0ub9ac uacbdub85c")
    parser.add_argument("--port", type=int, default=8000, help="uc11cube44uc2a4 ud3ecud2b8")
    parser.add_argument("--api-key", help="uc0acuc6a9ud560 API ud0a4 (ud074ub77cuad6c ubaa8ub4dc)")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        # uc11cube44uc2a4 ubaa8ub4dc
        run_mcp_server(data_dir=args.data_dir, port=args.port)
    else:
        # ud074ub77cuad6c ubaa8ub4dc
        api_key = args.api_key
        
        if not api_key:
            # API ud0a4uac00 uc5c6uc73cuba74 uc0c8ub85c uc0dduc131 uc2dcuacc4
            print("API ud0a4uac00 uc5c6uc2b5ub2c8ub2e4. uc0c8 API ud0a4ub97c uc0dduc131ud569ub2c8ub2e4...")
            api_key = create_api_key()
            
            if not api_key:
                print("API ud0a4 uc0dduc131uc5d0 uc2e4ud328ud588uc2b5ub2c8ub2e4. uc11cube44uc2a4uac00 uc2e4ud589 uc911uc778uc9c0 ud655uc778ud574uc8fc uc138uc694.")
                return
        
        # uae30uc5b5 uc791uc5c5 ud14cuc2a4ud2b8
        test_memory_operations(api_key)
        
        # Unity uc5f0ub3d9 ud14cuc2a4ud2b8
        test_unity_integration(api_key)

if __name__ == "__main__":
    main() 