import logging
from typing import Dict, Any, List, Optional, Union
import os
import json

# MemoryEngine uad00ub828 ubaa8ub4c8 uc784ud3ecud2b8
from memory_engine.block_manager import BlockManager
from memory_engine.cache_manager import CacheManager
from memory_engine.prompt_wrapper import PromptWrapper

class MCPIntegrations:
    """
    Cursor MCP uc5f0ub3d9 ud074ub798uc2a4
    Unity, Discord ub4f1uc758 MCP uad6cuc131uc694uc18cuc640 MemoryEngineuc744 uc5f0ub3d9ud558ub294 uae30ub2a5 uad6cud604
    """
    
    def __init__(self, data_dir: str = "./data", config_path: str = "./data/mcp_config.json"):
        """
        MCP uc5f0ub3d9 ud074ub798uc2a4 ucd08uae30ud654
        
        Args:
            data_dir: ub370uc774ud130 ub514ub809ud1a0ub9ac uacbdub85c
            config_path: MCP uad6cuc131 ud30cuc77c uacbdub85c
        """
        self.data_dir = data_dir
        self.config_path = config_path
        
        # ub85cuae45 uc124uc815
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("MCPIntegrations")
        
        # MemoryEngine ucef4ud3ecub10cud2b8 ucd08uae30ud654
        os.makedirs(data_dir, exist_ok=True)
        self.block_manager = BlockManager(data_dir=data_dir)
        self.cache_manager = CacheManager(data_dir=data_dir)
        self.prompt_wrapper = PromptWrapper()
        
        # uad6cuc131 ud30cuc77c ubd88ub7ecuc624uae30 ub610ub294 uae30ubcf8uac12 uc0dduc131
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """
        MCP uad6cuc131 ud30cuc77c ubd88ub7ecuc624uae30 ub610ub294 uae30ubcf8uac12 uc0dduc131
        
        Returns:
            uad6cuc131 uc815ubcf4
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"uad6cuc131 ud30cuc77c ub85cub4dc uc624ub958: {e}")
        
        # uae30ubcf8 uad6cuc131 uc0dduc131
        default_config = {
            "unity": {
                "enabled": False,
                "base_url": "http://localhost:8000/api/mcp/unity",
                "api_key": ""
            },
            "discord": {
                "enabled": False,
                "token": "",
                "guild_id": ""
            },
            "memory_tags": {
                "unity": ["unity", "gamedev", "game", "3d"],
                "discord": ["discord", "chat", "message", "communication"]
            }
        }
        
        # uae30ubcf8 uad6cuc131 uc800uc7a5
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def save_config(self) -> bool:
        """
        MCP uad6cuc131 ud30cuc77c uc800uc7a5
        
        Returns:
            uc131uacf5 uc5ecubd80
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"uad6cuc131 ud30cuc77c uc800uc7a5 uc624ub958: {e}")
            return False
    
    def unity_event_to_memory(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Unity uc774ubca4ud2b8ub97c uae30uc5b5uc73cub85c ubcc0ud658
        
        Args:
            event_type: uc774ubca4ud2b8 ud0c0uc785
            event_data: uc774ubca4ud2b8 ub370uc774ud130
            
        Returns:
            uae30uc5b5 ub0b4uc6a9 ubb38uc790uc5f4
        """
        memory_content = ""
        
        if event_type == "menu_item_executed":
            memory_content = f"Unity uba54ub274 uc544uc774ud15c '{event_data.get('menuPath')}'uc744(ub97c) uc2e4ud589ud588uc2b5ub2c8ub2e4."
        
        elif event_type == "gameobject_selected":
            obj_path = event_data.get("objectPath", "")
            instance_id = event_data.get("instanceId", "")
            if obj_path:
                memory_content = f"Unityuc5d0uc11c '{obj_path}' uac8cuc784uc624ube0cuc81dud2b8ub97c uc120ud0ddud588uc2b5ub2c8ub2e4."
            elif instance_id:
                memory_content = f"Unityuc5d0uc11c uc778uc2a4ud134uc2a4 ID {instance_id}uc758 uac8cuc784uc624ube0cuc81dud2b8ub97c uc120ud0ddud588uc2b5ub2c8ub2e4."
        
        elif event_type == "package_added":
            source = event_data.get("source", "")
            package_name = event_data.get("packageName", "")
            memory_content = f"Unityuc5d0 {source} uc18cuc2a4uc5d0uc11c {package_name} ud328ud0a4uc9c0ub97c ucd94uac00ud588uc2b5ub2c8ub2e4."
        
        elif event_type == "tests_run":
            test_mode = event_data.get("testMode", "")
            test_filter = event_data.get("testFilter", "")
            if test_filter:
                memory_content = f"Unityuc5d0uc11c {test_mode} ubaa8ub4dcuc5d0uc11c '{test_filter}' ud544ud130ub85c ud14cuc2a4ud2b8ub97c uc2e4ud589ud588uc2b5ub2c8ub2e4."
            else:
                memory_content = f"Unityuc5d0uc11c {test_mode} ubaa8ub4dcuc758 ud14cuc2a4ud2b8ub97c uc2e4ud589ud588uc2b5ub2c8ub2e4."
        
        elif event_type == "console_log":
            message = event_data.get("message", "")
            log_type = event_data.get("type", "info")
            memory_content = f"Unity ucf58uc194uc5d0 {log_type} ub808ubca8 ub85cuadf8: {message}"
        
        elif event_type == "component_updated":
            component_name = event_data.get("componentName", "")
            object_path = event_data.get("objectPath", "")
            memory_content = f"Unityuc5d0uc11c '{object_path}' uac8cuc784uc624ube0cuc81dud2b8uc758 {component_name} ucef4ud3ecub10cud2b8ub97c uc5c5ub370uc774ud2b8ud588uc2b5ub2c8ub2e4."
        
        elif event_type == "asset_added":
            asset_path = event_data.get("assetPath", "")
            memory_content = f"Unity uc52cuc5d0 {asset_path} uc5d0uc14buc744 ucd94uac00ud588uc2b5ub2c8ub2e4."
        
        else:
            # uae30ubcf8 ud615uc2dduc758 uae30uc5b5 uc0dduc131
            memory_content = f"Unity {event_type} uc774ubca4ud2b8: {json.dumps(event_data, ensure_ascii=False)}"
        
        return memory_content
    
    def discord_event_to_memory(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Discord uc774ubca4ud2b8ub97c uae30uc5b5uc73cub85c ubcc0ud658
        
        Args:
            event_type: uc774ubca4ud2b8 ud0c0uc785
            event_data: uc774ubca4ud2b8 ub370uc774ud130
            
        Returns:
            uae30uc5b5 ub0b4uc6a9 ubb38uc790uc5f4
        """
        memory_content = ""
        
        if event_type == "message_sent":
            channel_id = event_data.get("channelId", "")
            message = event_data.get("message", "")
            memory_content = f"Discord ucc44ub110 {channel_id}uc5d0 uba54uc2dcuc9c0 ubc1cuc1a1: {message}"
        
        elif event_type == "forum_post_created":
            forum_channel_id = event_data.get("forumChannelId", "")
            title = event_data.get("title", "")
            content = event_data.get("content", "")
            memory_content = f"Discord ud3ecub7fc ucc44ub110 {forum_channel_id}uc5d0 '{title}' uc81cubaa9uc758 uac8cuc2dcubb3c uc0dduc131"
        
        elif event_type == "forum_post_reply":
            thread_id = event_data.get("threadId", "")
            message = event_data.get("message", "")
            memory_content = f"Discord ud3ecub7fc uc2a4ub808ub4dc {thread_id}uc5d0 ub2f5ubcc0 uc791uc131"
        
        elif event_type == "reaction_added":
            channel_id = event_data.get("channelId", "")
            message_id = event_data.get("messageId", "")
            emoji = event_data.get("emoji", "")
            memory_content = f"Discord ucc44ub110 {channel_id}uc758 uba54uc2dcuc9c0 {message_id}uc5d0 {emoji} ubc18uc751 ucd94uac00"
        
        else:
            # uae30ubcf8 ud615uc2dduc758 uae30uc5b5 uc0dduc131
            memory_content = f"Discord {event_type} uc774ubca4ud2b8: {json.dumps(event_data, ensure_ascii=False)}"
        
        return memory_content
    
    def store_unity_event(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Unity uc774ubca4ud2b8ub97c uae30uc5b5uc73cub85c uc800uc7a5
        
        Args:
            event_type: uc774ubca4ud2b8 ud0c0uc785
            event_data: uc774ubca4ud2b8 ub370uc774ud130
            
        Returns:
            uc0dduc131ub41c uae30uc5b5 ID
        """
        memory_content = self.unity_event_to_memory(event_type, event_data)
        # ud0dcuadf8 ucd94uac00
        tags = self.config.get("memory_tags", {}).get("unity", [])
        memory_content = f"[{', '.join(tags)}] {memory_content}"
        
        # uae30uc5b5 uc800uc7a5
        memory_id = self.block_manager.add_memory(memory_content)
        # uce90uc2dc uc5c5ub370uc774ud2b8
        self.cache_manager.update_cache()
        
        return memory_id
    
    def store_discord_event(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Discord uc774ubca4ud2b8ub97c uae30uc5b5uc73cub85c uc800uc7a5
        
        Args:
            event_type: uc774ubca4ud2b8 ud0c0uc785
            event_data: uc774ubca4ud2b8 ub370uc774ud130
            
        Returns:
            uc0dduc131ub41c uae30uc5b5 ID
        """
        memory_content = self.discord_event_to_memory(event_type, event_data)
        # ud0dcuadf8 ucd94uac00
        tags = self.config.get("memory_tags", {}).get("discord", [])
        memory_content = f"[{', '.join(tags)}] {memory_content}"
        
        # uae30uc5b5 uc800uc7a5
        memory_id = self.block_manager.add_memory(memory_content)
        # uce90uc2dc uc5c5ub370uc774ud2b8
        self.cache_manager.update_cache()
        
        return memory_id
    
    def get_related_unity_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Unity uad00ub828 uae30uc5b5 uac80uc0c9
        
        Args:
            query: uac80uc0c9 ucffcub9ac
            limit: uacb0uacfc uac1cuc218 uc81cud55c
            
        Returns:
            uac80uc0c9 uacb0uacfc ubaa9ub85d
        """
        # Unity ud0dcuadf8uac00 uc788ub294 uae30uc5b5ub9cc uac80uc0c9
        tags = self.config.get("memory_tags", {}).get("unity", [])
        tagged_query = f"({' OR '.join(tags)}) AND {query}"
        
        results = self.cache_manager.search(tagged_query, limit=limit)
        return results
    
    def get_related_discord_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Discord uad00ub828 uae30uc5b5 uac80uc0c9
        
        Args:
            query: uac80uc0c9 ucffcub9ac
            limit: uacb0uacfc uac1cuc218 uc81cud55c
            
        Returns:
            uac80uc0c9 uacb0uacfc ubaa9ub85d
        """
        # Discord ud0dcuadf8uac00 uc788ub294 uae30uc5b5ub9cc uac80uc0c9
        tags = self.config.get("memory_tags", {}).get("discord", [])
        tagged_query = f"({' OR '.join(tags)}) AND {query}"
        
        results = self.cache_manager.search(tagged_query, limit=limit)
        return results 