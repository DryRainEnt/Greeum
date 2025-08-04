import unittest
import time
from tests.base_test_case import BaseGreeumTestCase
from greeum.core.working_memory import STMWorkingSet


class TestSTMWorkingSet(BaseGreeumTestCase):
    """STMWorkingSet 테스트 클래스"""
    
    def test_add_and_get_recent(self):
        """최근 항목 추가 및 조회 테스트"""
        wm = STMWorkingSet(capacity=3, ttl_seconds=60)
        wm.add("a")
        wm.add("b")
        wm.add("c")
        recent = [slot.content for slot in wm.get_recent()]
        self.assertEqual(recent, ["c", "b", "a"])

    def test_capacity_trim(self):
        """용량 초과 시 trim 테스트"""
        wm = STMWorkingSet(capacity=2, ttl_seconds=60)
        wm.add("x")
        wm.add("y")
        wm.add("z")  # should evict "x"
        recent = [slot.content for slot in wm.get_recent()]
        self.assertEqual(recent, ["z", "y"])

    def test_ttl_expiry(self):
        """TTL 만료 테스트"""
        wm = STMWorkingSet(capacity=3, ttl_seconds=1)
        wm.add("m1")
        time.sleep(1.2)
        wm.add("m2")
        recent = [slot.content for slot in wm.get_recent()]
        self.assertEqual(recent, ["m2"])


if __name__ == '__main__':
    unittest.main() 