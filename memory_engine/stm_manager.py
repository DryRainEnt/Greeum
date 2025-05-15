import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

class STMManager:
    """단기 기억(Short-Term Memory)을 관리하는 클래스"""
    
    def __init__(self, data_path: str = "data/short_term.json", ttl: int = 3600):
        """
        단기 기억 매니저 초기화
        
        Args:
            data_path: STM 데이터 파일 경로
            ttl: Time-To-Live (초 단위, 기본값 1시간)
        """
        self.data_path = data_path
        self.ttl = ttl
        self._ensure_data_file()
        self.stm_data = self._load_stm()
        
    def _ensure_data_file(self) -> None:
        """데이터 파일이 존재하는지 확인하고 없으면 생성"""
        data_dir = os.path.dirname(self.data_path)
        os.makedirs(data_dir, exist_ok=True)
        
        if not os.path.exists(self.data_path):
            default_data = {
                "memories": [],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def _load_stm(self) -> Dict[str, Any]:
        """STM 데이터 로드"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError:
            # 파일이 비어있거나 손상된 경우
            return {"memories": [], "last_updated": datetime.now().isoformat()}
    
    def _save_stm(self) -> None:
        """STM 데이터 저장"""
        self.stm_data["last_updated"] = datetime.now().isoformat()
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.stm_data, f, ensure_ascii=False, indent=2)
    
    def clean_expired(self) -> None:
        """만료된 기억 제거"""
        current_time = time.time()
        memories = self.stm_data.get("memories", [])
        valid_memories = []
        
        for memory in memories:
            timestamp = memory.get("timestamp", 0)
            # 타임스탬프가 문자열인 경우 (ISO 형식)
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.timestamp()
                except ValueError:
                    # 잘못된 형식의 타임스탬프는 무시
                    timestamp = 0
            
            if current_time - timestamp < self.ttl:
                valid_memories.append(memory)
        
        self.stm_data["memories"] = valid_memories
        self._save_stm()
    
    def add_memory(self, memory_data: Dict[str, Any]) -> None:
        """
        단기 기억 추가
        
        Args:
            memory_data: 기억 데이터 (타임스탬프가 포함되어 있어야 함)
        """
        if "timestamp" not in memory_data:
            memory_data["timestamp"] = datetime.now().isoformat()
            
        self.stm_data["memories"].append(memory_data)
        self._save_stm()
        
        # 주기적으로 만료된 기억 제거
        self.clean_expired()
    
    def get_recent_memories(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        최근 기억 조회
        
        Args:
            count: 반환할 기억 개수
            
        Returns:
            최근 기억 목록
        """
        # 먼저 만료된 기억 제거
        self.clean_expired()
        
        # 최신순으로 정렬
        memories = self.stm_data.get("memories", [])
        sorted_memories = sorted(
            memories, 
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        return sorted_memories[:count]
    
    def clear_all(self) -> None:
        """모든 단기 기억 삭제"""
        self.stm_data["memories"] = []
        self._save_stm()
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """ID로 기억 조회"""
        for memory in self.stm_data.get("memories", []):
            if memory.get("id") == memory_id:
                return memory
        return None 